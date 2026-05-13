#include <atomic>
#include <algorithm>
#include <cctype>
#include <chrono>
#include <iostream>
#include <optional>
#include <string>
#include <string_view>
#include <thread>
#include <unordered_map>
#include <vector>

#include "td/telegram/td_json_client.h"

namespace {
long long monotonic_now_ns() {
  const auto now = std::chrono::steady_clock::now().time_since_epoch();
  return std::chrono::duration_cast<std::chrono::nanoseconds>(now).count();
}

constexpr uint32_t MARKET_FLAG_KRW = 1;
constexpr uint32_t MARKET_FLAG_BTC = 2;
constexpr uint32_t MARKET_FLAG_USDT = 4;
constexpr uint32_t MARKET_FLAG_ETH = 8;

constexpr std::string_view MARKET_CODES[] = {"KRW", "BTC", "USDT", "ETH"};
constexpr std::string_view UPBIT_LISTING_KEYWORDS[] = {
    "신규 거래지원",
    "KRW 마켓 디지털 자산 추가",
    "BTC 마켓 디지털 자산 추가",
    "USDT 마켓 디지털 자산 추가",
};
constexpr std::string_view UPBIT_EXCLUDE_KEYWORDS[] = {
    "입출금",
    "유통량",
    "거래유의",
    "유의종목",
    "스테이킹",
    "이벤트",
    "종료",
    "변경 안내",
};
constexpr std::string_view BITHUMB_LISTING_KEYWORDS[] = {
    "[마켓 추가]",
    "원화 마켓 추가",
};
constexpr std::string_view BITHUMB_EXCLUDE_KEYWORDS[] = {
    "입출금",
    "유의촉구",
    "거래유의",
    "시세알림",
    "종료",
};

struct ListingMatch {
  std::string exchange;
  std::string signal_type;
  std::string ticker;
  std::string asset_name;
  uint32_t market_flags{0};
};

std::string json_escape(const std::string& input) {
  std::string escaped;
  escaped.reserve(input.size());
  for (const char ch : input) {
    switch (ch) {
      case '\\':
        escaped += "\\\\";
        break;
      case '"':
        escaped += "\\\"";
        break;
      case '\n':
        escaped += "\\n";
        break;
      case '\r':
        escaped += "\\r";
        break;
      case '\t':
        escaped += "\\t";
        break;
      default:
        escaped.push_back(ch);
        break;
    }
  }
  return escaped;
}

std::optional<long long> extract_json_int(const std::string& body, const std::string& key) {
  const std::string pattern = "\"" + key + "\":";
  size_t pos = body.find(pattern);
  if (pos == std::string::npos) {
    return std::nullopt;
  }
  pos += pattern.size();
  while (pos < body.size() && std::isspace(static_cast<unsigned char>(body[pos]))) {
    ++pos;
  }
  size_t end = pos;
  if (end < body.size() && (body[end] == '-' || body[end] == '+')) {
    ++end;
  }
  while (end < body.size() && std::isdigit(static_cast<unsigned char>(body[end]))) {
    ++end;
  }
  if (end == pos) {
    return std::nullopt;
  }
  return std::stoll(body.substr(pos, end - pos));
}

std::optional<std::string> extract_json_string(const std::string& body, const std::string& key, size_t start_pos = 0) {
  const std::string pattern = "\"" + key + "\":";
  size_t pos = body.find(pattern, start_pos);
  if (pos == std::string::npos) {
    return std::nullopt;
  }
  pos = body.find('"', pos + pattern.size());
  if (pos == std::string::npos) {
    return std::nullopt;
  }
  ++pos;
  std::string result;
  bool escaped = false;
  for (; pos < body.size(); ++pos) {
    const char ch = body[pos];
    if (escaped) {
      result.push_back(ch);
      escaped = false;
      continue;
    }
    if (ch == '\\') {
      escaped = true;
      continue;
    }
    if (ch == '"') {
      return result;
    }
    result.push_back(ch);
  }
  return std::nullopt;
}

bool contains_any(std::string_view title, const std::string_view* keywords, size_t count) {
  for (size_t i = 0; i < count; ++i) {
    if (title.find(keywords[i]) != std::string_view::npos) {
      return true;
    }
  }
  return false;
}

bool contains_none(std::string_view title, const std::string_view* keywords, size_t count) {
  for (size_t i = 0; i < count; ++i) {
    if (title.find(keywords[i]) != std::string_view::npos) {
      return false;
    }
  }
  return true;
}

bool is_ascii_word_char(char ch) {
  return std::isalnum(static_cast<unsigned char>(ch)) != 0 || ch == '_';
}

bool has_ascii_word(std::string_view title, std::string_view needle) {
  size_t pos = 0;
  while (true) {
    pos = title.find(needle, pos);
    if (pos == std::string_view::npos) {
      return false;
    }
    const bool left_ok = pos == 0 || !is_ascii_word_char(title[pos - 1]);
    const size_t right = pos + needle.size();
    const bool right_ok = right >= title.size() || !is_ascii_word_char(title[right]);
    if (left_ok && right_ok) {
      return true;
    }
    pos = right;
  }
}

std::vector<std::string> extract_ticker_candidates(std::string_view title) {
  std::vector<std::string> candidates;
  for (size_t i = 0; i < title.size(); ++i) {
    if (title[i] != '(') {
      continue;
    }
    const size_t end = title.find(')', i + 1);
    if (end == std::string_view::npos) {
      break;
    }
    const auto candidate = title.substr(i + 1, end - i - 1);
    if (candidate.size() < 2 || candidate.size() > 10) {
      i = end;
      continue;
    }
    bool valid = true;
    for (char ch : candidate) {
      if (!(std::isupper(static_cast<unsigned char>(ch)) || std::isdigit(static_cast<unsigned char>(ch)))) {
        valid = false;
        break;
      }
    }
    if (valid) {
      candidates.emplace_back(candidate);
    }
    i = end;
  }
  return candidates;
}

bool is_market_code(std::string_view candidate) {
  for (auto code : MARKET_CODES) {
    if (candidate == code) {
      return true;
    }
  }
  return false;
}

std::string extract_primary_ticker(std::string_view title) {
  const auto candidates = extract_ticker_candidates(title);
  for (const auto& candidate : candidates) {
    if (!is_market_code(candidate)) {
      return candidate;
    }
  }
  return "";
}

uint32_t extract_market_flags(std::string_view title) {
  uint32_t flags = 0;
  if (title.find("원화 마켓") != std::string_view::npos || has_ascii_word(title, "KRW")) {
    flags |= MARKET_FLAG_KRW;
  }
  if (has_ascii_word(title, "BTC")) {
    flags |= MARKET_FLAG_BTC;
  }
  if (has_ascii_word(title, "USDT")) {
    flags |= MARKET_FLAG_USDT;
  }
  if (has_ascii_word(title, "ETH")) {
    flags |= MARKET_FLAG_ETH;
  }
  if (flags != 0) {
    return flags;
  }
  for (const auto& candidate : extract_ticker_candidates(title)) {
    if (candidate == "KRW") {
      flags |= MARKET_FLAG_KRW;
    } else if (candidate == "BTC") {
      flags |= MARKET_FLAG_BTC;
    } else if (candidate == "USDT") {
      flags |= MARKET_FLAG_USDT;
    } else if (candidate == "ETH") {
      flags |= MARKET_FLAG_ETH;
    }
  }
  return flags;
}

std::string trim_ascii(std::string value) {
  auto is_space = [](unsigned char ch) { return std::isspace(ch) != 0; };
  value.erase(value.begin(), std::find_if(value.begin(), value.end(), [&](char ch) {
                return !is_space(static_cast<unsigned char>(ch));
              }));
  value.erase(std::find_if(value.rbegin(), value.rend(), [&](char ch) {
                return !is_space(static_cast<unsigned char>(ch));
              }).base(),
              value.end());
  return value;
}

bool parse_market_parenthetical(std::string_view candidate) {
  std::string normalized = trim_ascii(std::string(candidate));
  candidate = normalized;
  constexpr std::string_view suffix = "마켓";
  if (candidate.size() < suffix.size() ||
      candidate.substr(candidate.size() - suffix.size()) != suffix) {
    return false;
  }
  candidate = candidate.substr(0, candidate.size() - suffix.size());
  normalized = trim_ascii(std::string(candidate));
  candidate = normalized;
  if (candidate.empty()) {
    return false;
  }
  size_t start = 0;
  bool matched = false;
  while (start < candidate.size()) {
    size_t comma = candidate.find(',', start);
    const size_t end = comma == std::string_view::npos ? candidate.size() : comma;
    const std::string part_str = trim_ascii(std::string(candidate.substr(start, end - start)));
    const auto part = std::string_view(part_str);
    if (part.empty() || !is_market_code(part)) {
      return false;
    }
    matched = true;
    if (comma == std::string_view::npos) {
      break;
    }
    start = comma + 1;
  }
  return matched;
}

size_t find_market_parenthetical_end(std::string_view title, size_t start = 0) {
  size_t search = start;
  while (true) {
    const size_t open = title.find('(', search);
    if (open == std::string_view::npos) {
      return std::string_view::npos;
    }
    const size_t close = title.find(')', open + 1);
    if (close == std::string_view::npos) {
      return std::string_view::npos;
    }
    if (parse_market_parenthetical(title.substr(open + 1, close - open - 1))) {
      return close + 1;
    }
    search = close + 1;
  }
}

std::string extract_asset_name(std::string_view title) {
  const size_t bracket = title.find(']');
  if (bracket == std::string_view::npos) {
    return trim_ascii(std::string(title));
  }
  const size_t open = title.find('(', bracket + 1);
  if (open == std::string_view::npos || open <= bracket + 1) {
    return trim_ascii(std::string(title));
  }
  return trim_ascii(std::string(title.substr(bracket + 1, open - bracket - 1)));
}

bool is_allowed_bithumb_market_add_suffix(std::string_view suffix) {
  const std::string trimmed = trim_ascii(std::string(suffix));
  if (trimmed.empty() ||
      trimmed == "및 재단 에어드랍 안내" ||
      trimmed == "및 에어드랍 안내") {
    return true;
  }
  constexpr std::string_view blocked[] = {
      "거래 오픈",
      "오픈 예정",
      "시간 변경",
      "연기",
      "입출금",
      "재거래지원",
      "유의",
      "중단",
      "종료",
  };
  for (auto keyword : blocked) {
    if (trimmed.find(keyword) != std::string::npos) {
      return false;
    }
  }
  const std::string suffix_end = " 안내";
  return trimmed.rfind("및 ", 0) == 0 &&
         trimmed.size() >= suffix_end.size() &&
         trimmed.compare(
             trimmed.size() - suffix_end.size(),
             suffix_end.size(),
             suffix_end) == 0;
}

bool is_upbit_listing(std::string_view title) {
  if (title.rfind("[거래]", 0) != 0 ||
      !contains_none(title, UPBIT_EXCLUDE_KEYWORDS, std::size(UPBIT_EXCLUDE_KEYWORDS))) {
    return false;
  }
  constexpr std::string_view new_listing_anchor = "신규 거래지원 안내";
  if (title.find(new_listing_anchor) != std::string_view::npos) {
    const size_t market_end = find_market_parenthetical_end(
        title,
        title.find(new_listing_anchor));
    return market_end != std::string_view::npos &&
           trim_ascii(std::string(title.substr(market_end))).empty();
  }
  constexpr std::string_view market_add_suffix = "마켓 디지털 자산 추가";
  const std::string trimmed = trim_ascii(std::string(title));
  const std::string suffix(market_add_suffix);
  return title.find(market_add_suffix) != std::string_view::npos &&
         trimmed.size() >= suffix.size() &&
         trimmed.compare(trimmed.size() - suffix.size(), suffix.size(), suffix) == 0;
}

bool is_bithumb_listing(std::string_view title) {
  if (title.rfind("[마켓 추가]", 0) != 0 ||
      !contains_none(title, BITHUMB_EXCLUDE_KEYWORDS, std::size(BITHUMB_EXCLUDE_KEYWORDS)) ||
      title.find("원화 마켓 재거래지원 안내") != std::string_view::npos) {
    return false;
  }
  constexpr std::string_view marker = "원화 마켓 추가";
  const size_t marker_pos = title.find(marker);
  if (marker_pos == std::string_view::npos) {
    return false;
  }
  return is_allowed_bithumb_market_add_suffix(
      title.substr(marker_pos + marker.size()));
}

std::optional<ListingMatch> classify_listing_title(const std::string& exchange, std::string_view title) {
  bool matched = false;
  std::string signal_type;
  if (exchange == "upbit") {
    matched = is_upbit_listing(title) && has_ascii_word(title, "KRW");
    signal_type = "new_listing";
  } else if (exchange == "bithumb") {
    matched = is_bithumb_listing(title) &&
              title.find("원화 마켓") != std::string_view::npos;
    signal_type = "market_add";
  } else {
    return std::nullopt;
  }

  if (!matched) {
    return std::nullopt;
  }
  const std::string ticker = extract_primary_ticker(title);
  if (ticker.empty()) {
    return std::nullopt;
  }
  return ListingMatch{
      exchange,
      signal_type,
      ticker,
      extract_asset_name(title),
      extract_market_flags(title),
  };
}

std::string exchange_from_handle(const std::string& handle) {
  if (handle == "upbit_news") {
    return "upbit";
  }
  if (handle == "BithumbExchange" || handle == "bithumbexchange") {
    return "bithumb";
  }
  return "";
}

std::string market_flags_json(uint32_t flags) {
  std::string result = "[";
  bool first = true;
  auto append = [&](const char* market) {
    if (!first) {
      result += ",";
    }
    first = false;
    result += "\"";
    result += market;
    result += "\"";
  };
  if (flags & MARKET_FLAG_KRW) {
    append("KRW");
  }
  if (flags & MARKET_FLAG_BTC) {
    append("BTC");
  }
  if (flags & MARKET_FLAG_USDT) {
    append("USDT");
  }
  if (flags & MARKET_FLAG_ETH) {
    append("ETH");
  }
  result += "]";
  return result;
}

std::unordered_map<long long, std::string> parse_watch_map(const std::string& spec) {
  std::unordered_map<long long, std::string> out;
  size_t start = 0;
  while (start < spec.size()) {
    size_t end = spec.find(',', start);
    const std::string item = spec.substr(start, end == std::string::npos ? std::string::npos : end - start);
    const size_t sep = item.find(':');
    if (sep != std::string::npos) {
      try {
        const long long chat_id = std::stoll(item.substr(0, sep));
        out[chat_id] = item.substr(sep + 1);
      } catch (...) {
      }
    }
    if (end == std::string::npos) {
      break;
    }
    start = end + 1;
  }
  return out;
}

bool maybe_emit_listing_matched(
    const std::string& result,
    const std::unordered_map<long long, std::string>& watched_chats,
    bool native_listing_mode) {
  if (!native_listing_mode) {
    return false;
  }
  if (result.find("\"@type\":\"updateNewMessage\"") == std::string::npos) {
    return false;
  }
  const auto chat_id = extract_json_int(result, "chat_id");
  if (!chat_id.has_value()) {
    return false;
  }
  const auto it = watched_chats.find(*chat_id);
  if (it == watched_chats.end()) {
    return false;
  }
  const std::string& handle = it->second;
  const std::string exchange = exchange_from_handle(handle);
  if (exchange.empty()) {
    return false;
  }

  const size_t content_pos = result.find("\"content\":");
  if (content_pos == std::string::npos ||
      result.find("\"@type\":\"messageText\"", content_pos) == std::string::npos) {
    return false;
  }
  const auto text = extract_json_string(result, "text", content_pos);
  if (!text.has_value() || text->empty()) {
    return false;
  }
  const auto listing = classify_listing_title(exchange, *text);
  if (!listing.has_value()) {
    return true;
  }

  const auto message_id = extract_json_int(result, "id");
  const auto published_at = extract_json_int(result, "date");
  if (!message_id.has_value() || !published_at.has_value()) {
    return true;
  }

  std::cout << monotonic_now_ns() << '\t'
            << "{\"@type\":\"listingMatched\","
            << "\"channel_handle\":\"" << json_escape(handle) << "\","
            << "\"exchange\":\"" << json_escape(listing->exchange) << "\","
            << "\"message_id\":" << *message_id << ","
            << "\"published_at_unix\":" << *published_at << ","
            << "\"title\":\"" << json_escape(*text) << "\","
            << "\"signal_type\":\"" << json_escape(listing->signal_type) << "\","
            << "\"ticker\":\"" << json_escape(listing->ticker) << "\","
            << "\"asset_name\":\"" << json_escape(listing->asset_name) << "\","
            << "\"markets\":" << market_flags_json(listing->market_flags)
            << "}" << std::endl;
  return true;
}
}  // namespace

int main() {
  td_json_client_execute(
      nullptr,
      R"({"@type":"setLogVerbosityLevel","new_verbosity_level":0})");

  void *client = td_json_client_create();
  std::atomic<bool> should_stop{false};
  std::atomic<bool> native_listing_mode{false};
  std::unordered_map<long long, std::string> watched_chats;

  std::thread stdin_thread([&]() {
    std::string line;
    while (std::getline(std::cin, line)) {
      if (!line.empty() && line.back() == '\r') {
        line.pop_back();
      }
      if (line == "__quit__") {
        should_stop.store(true);
        break;
      }
      if (line == "__clock__") {
        std::cout << "__clock__\t" << monotonic_now_ns() << std::endl;
        continue;
      }
      if (line == "__native_listing_on__") {
        native_listing_mode.store(true);
        continue;
      }
      if (line == "__native_listing_off__") {
        native_listing_mode.store(false);
        continue;
      }
      if (line.rfind("__watch_chats__\t", 0) == 0) {
        watched_chats = parse_watch_map(line.substr(std::string("__watch_chats__\t").size()));
        continue;
      }
      if (!line.empty()) {
        td_json_client_send(client, line.c_str());
      }
    }
    should_stop.store(true);
  });

  std::cout << "__relay_ready__" << std::endl;

  while (!should_stop.load()) {
    if (const char *result = td_json_client_receive(client, 0.001)) {
      const std::string payload(result);
      if (maybe_emit_listing_matched(payload, watched_chats, native_listing_mode.load())) {
        continue;
      }
      std::cout << monotonic_now_ns() << '\t' << payload << std::endl;
    }
  }

  td_json_client_destroy(client);
  if (stdin_thread.joinable()) {
    stdin_thread.join();
  }
  return 0;
}
