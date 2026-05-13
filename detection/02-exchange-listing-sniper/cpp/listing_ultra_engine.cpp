#include <curl/curl.h>
#include <openssl/hmac.h>

#include <algorithm>
#include <cctype>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <iomanip>
#include <mutex>
#include <optional>
#include <sstream>
#include <string>
#include <string_view>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace {

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

struct NativeUltraResult {
    int matched;
    int duplicate;
    uint32_t market_flags;
    int attempted;
    int executed;
    int ret_code;
    char ticker[16];
    char asset_name[128];
    char signal_type[16];
    char symbol[24];
    char order_id[64];
    char order_link_id[40];
    char transport[32];
    char reason[128];
};

struct HttpResult {
    long status_code{0};
    std::string body;
    std::string error;
    bool success{false};
};

size_t write_callback(void* contents, size_t size, size_t nmemb, void* userp) {
    const size_t total = size * nmemb;
    auto* output = static_cast<std::string*>(userp);
    output->append(static_cast<char*>(contents), total);
    return total;
}

std::string getenv_or(const char* key, const char* fallback = "") {
    const char* value = std::getenv(key);
    return value ? std::string(value) : std::string(fallback);
}

bool getenv_truthy(const char* key, bool fallback = false) {
    const char* value = std::getenv(key);
    if (value == nullptr) {
        return fallback;
    }
    std::string text(value);
    std::transform(text.begin(), text.end(), text.begin(), [](unsigned char ch) {
        return static_cast<char>(std::tolower(ch));
    });
    return text == "1" || text == "true" || text == "yes" || text == "on";
}

std::string json_escape(const std::string& input) {
    std::ostringstream escaped;
    for (const char ch : input) {
        switch (ch) {
            case '\\':
                escaped << "\\\\";
                break;
            case '"':
                escaped << "\\\"";
                break;
            case '\n':
                escaped << "\\n";
                break;
            case '\r':
                escaped << "\\r";
                break;
            case '\t':
                escaped << "\\t";
                break;
            default:
                escaped << ch;
        }
    }
    return escaped.str();
}

std::optional<std::string> extract_json_string(const std::string& body, const std::string& key) {
    const std::string pattern = "\"" + key + "\":";
    size_t pos = body.find(pattern);
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

std::vector<std::string> extract_symbols(const std::string& body) {
    std::vector<std::string> symbols;
    const std::string needle = "\"symbol\":\"";
    size_t pos = 0;
    while (true) {
        pos = body.find(needle, pos);
        if (pos == std::string::npos) {
            break;
        }
        pos += needle.size();
        size_t end = body.find('"', pos);
        if (end == std::string::npos) {
            break;
        }
        symbols.push_back(body.substr(pos, end - pos));
        pos = end + 1;
    }
    return symbols;
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
               suffix_end
           ) == 0;
}

void copy_to_buffer(const std::string& value, char* output, size_t capacity) {
    if (capacity == 0) {
        return;
    }
    std::memset(output, 0, capacity);
    const size_t len = std::min(value.size(), capacity - 1);
    std::memcpy(output, value.data(), len);
}

class CurlClient {
public:
    explicit CurlClient(std::string base_url)
        : base_url_(std::move(base_url)) {
        curl_global_init(CURL_GLOBAL_DEFAULT);
        curl_ = curl_easy_init();
    }

    ~CurlClient() {
        if (curl_ != nullptr) {
            curl_easy_cleanup(curl_);
        }
        curl_global_cleanup();
    }

    HttpResult get(const std::string& path, const std::vector<std::string>& headers = {}) {
        return perform("GET", path, "", headers);
    }

    HttpResult post(const std::string& path, const std::string& body, const std::vector<std::string>& headers = {}) {
        return perform("POST", path, body, headers);
    }

    std::string escape(const std::string& value) {
        if (curl_ == nullptr) {
            return value;
        }
        char* encoded = curl_easy_escape(curl_, value.c_str(), static_cast<int>(value.size()));
        if (encoded == nullptr) {
            return value;
        }
        std::string result(encoded);
        curl_free(encoded);
        return result;
    }

private:
    HttpResult perform(const std::string& method, const std::string& path, const std::string& body, const std::vector<std::string>& headers) {
        HttpResult result;
        if (curl_ == nullptr) {
            result.error = "curl_init_failed";
            return result;
        }
        curl_easy_reset(curl_);
        curl_easy_setopt(curl_, CURLOPT_URL, (base_url_ + path).c_str());
        curl_easy_setopt(curl_, CURLOPT_WRITEFUNCTION, write_callback);
        curl_easy_setopt(curl_, CURLOPT_WRITEDATA, &result.body);
        curl_easy_setopt(curl_, CURLOPT_TIMEOUT, 10L);
        curl_easy_setopt(curl_, CURLOPT_TCP_KEEPALIVE, 1L);
        curl_easy_setopt(curl_, CURLOPT_NOSIGNAL, 1L);
        curl_easy_setopt(curl_, CURLOPT_USERAGENT, "ChainPulse-UltraEngine/1.0");

        struct curl_slist* header_list = nullptr;
        for (const auto& header : headers) {
            header_list = curl_slist_append(header_list, header.c_str());
        }
        if (header_list != nullptr) {
            curl_easy_setopt(curl_, CURLOPT_HTTPHEADER, header_list);
        }
        if (method == "POST") {
            curl_easy_setopt(curl_, CURLOPT_POST, 1L);
            curl_easy_setopt(curl_, CURLOPT_POSTFIELDS, body.c_str());
            curl_easy_setopt(curl_, CURLOPT_POSTFIELDSIZE, body.size());
        } else {
            curl_easy_setopt(curl_, CURLOPT_HTTPGET, 1L);
        }

        const CURLcode code = curl_easy_perform(curl_);
        if (code != CURLE_OK) {
            result.error = curl_easy_strerror(code);
        } else {
            curl_easy_getinfo(curl_, CURLINFO_RESPONSE_CODE, &result.status_code);
            result.success = result.status_code >= 200 && result.status_code < 300;
        }

        if (header_list != nullptr) {
            curl_slist_free_all(header_list);
        }
        return result;
    }

    std::string base_url_;
    CURL* curl_{nullptr};
};

class ListingUltraEngine {
public:
    ListingUltraEngine()
        : api_key_(getenv_or("BYBIT_API_KEY")),
          api_secret_(getenv_or("BYBIT_API_SECRET")),
          base_url_(getenv_or("BYBIT_API_BASE_URL", "https://api.bybit.com")),
          recv_window_(getenv_or("BYBIT_RECV_WINDOW", "5000")),
          buy_enabled_(getenv_truthy("BYBIT_SPOT_BUY_ENABLED", false)),
          buy_quote_amount_(getenv_or("BYBIT_SPOT_BUY_USDT_AMOUNT", "0")),
          cache_only_symbol_check_(getenv_truthy("BYBIT_PREFER_CACHED_SYMBOL_CHECK", true)),
          client_(base_url_) {}

    int warmup() {
        std::lock_guard<std::mutex> lock(mu_);
        return refresh_symbols() ? 0 : -1;
    }

    int handle(std::string_view exchange, long long message_id, std::string_view title, NativeUltraResult* out) {
        if (out == nullptr) {
            return -1;
        }
        std::lock_guard<std::mutex> lock(mu_);
        std::memset(out, 0, sizeof(NativeUltraResult));

        const std::string dedup_key = std::string(exchange) + ":" + std::to_string(message_id);
        auto [_, inserted] = seen_keys_.insert(dedup_key);
        if (!inserted) {
            out->duplicate = 1;
            copy_to_buffer("duplicate", out->reason, sizeof(out->reason));
            return 1;
        }

        bool matched = false;
        std::string signal_type;
        if (exchange == "upbit") {
            matched = false;
            if (title.rfind("[거래]", 0) == 0 &&
                contains_none(title, UPBIT_EXCLUDE_KEYWORDS, std::size(UPBIT_EXCLUDE_KEYWORDS)) &&
                has_ascii_word(title, "KRW")) {
                constexpr std::string_view new_listing_anchor = "신규 거래지원 안내";
                if (title.find(new_listing_anchor) != std::string_view::npos) {
                    const size_t market_end = find_market_parenthetical_end(
                        title,
                        title.find(new_listing_anchor)
                    );
                    matched = market_end != std::string_view::npos &&
                              trim_ascii(std::string(title.substr(market_end))).empty();
                } else {
                    constexpr std::string_view market_add_suffix = "마켓 디지털 자산 추가";
                    const std::string trimmed = trim_ascii(std::string(title));
                    const std::string suffix(market_add_suffix);
                    matched = title.find(market_add_suffix) != std::string_view::npos &&
                              trimmed.size() >= suffix.size() &&
                              trimmed.compare(trimmed.size() - suffix.size(), suffix.size(), suffix) == 0;
                }
            }
            signal_type = "new_listing";
        } else if (exchange == "bithumb") {
            matched = false;
            if (title.rfind("[마켓 추가]", 0) == 0 &&
                contains_none(title, BITHUMB_EXCLUDE_KEYWORDS, std::size(BITHUMB_EXCLUDE_KEYWORDS)) &&
                title.find("원화 마켓 재거래지원 안내") == std::string_view::npos) {
                constexpr std::string_view marker = "원화 마켓 추가";
                const size_t marker_pos = title.find(marker);
                matched = marker_pos != std::string_view::npos &&
                          is_allowed_bithumb_market_add_suffix(
                              title.substr(marker_pos + marker.size())
                          );
            }
            signal_type = "market_add";
        } else {
            return 0;
        }

        if (!matched) {
            return 0;
        }

        const std::string ticker = extract_primary_ticker(title);
        if (ticker.empty()) {
            return 0;
        }

        out->matched = 1;
        out->market_flags = extract_market_flags(title);
        copy_to_buffer(ticker, out->ticker, sizeof(out->ticker));
        copy_to_buffer(extract_asset_name(title), out->asset_name, sizeof(out->asset_name));
        copy_to_buffer(signal_type, out->signal_type, sizeof(out->signal_type));

        const std::string symbol = ticker + "USDT";
        copy_to_buffer(symbol, out->symbol, sizeof(out->symbol));
        const std::string order_link_id =
            ("ls-" + std::string(exchange) + "-" + std::to_string(message_id) + "-" + ticker);
        copy_to_buffer(order_link_id.substr(0, 36), out->order_link_id, sizeof(out->order_link_id));

        if (!buy_enabled_) {
            copy_to_buffer("buy_disabled", out->reason, sizeof(out->reason));
            return 1;
        }
        if (api_key_.empty() || api_secret_.empty()) {
            copy_to_buffer("missing_api_config", out->reason, sizeof(out->reason));
            return 1;
        }
        if (!has_spot_symbol(symbol)) {
            copy_to_buffer("spot_symbol_unavailable", out->reason, sizeof(out->reason));
            return 1;
        }

        out->attempted = 1;
        const std::string body =
            "{\"category\":\"spot\",\"symbol\":\"" + symbol +
            "\",\"side\":\"Buy\",\"orderType\":\"Market\",\"qty\":\"" + buy_quote_amount_ +
            "\",\"orderFilter\":\"Order\",\"marketUnit\":\"quoteCoin\",\"orderLinkId\":\"" +
            order_link_id.substr(0, 36) + "\"}";
        const auto response = client_.post("/v5/order/create", body, auth_headers(body));
        const long long ret_code = extract_json_int(response.body, "retCode").value_or(-1);
        out->ret_code = static_cast<int>(ret_code);
        if (!response.success || ret_code != 0) {
            const std::string reason =
                extract_json_string(response.body, "retMsg").value_or(
                    response.error.empty() ? "order_create_failed" : response.error
                );
            copy_to_buffer(reason, out->reason, sizeof(out->reason));
            copy_to_buffer("cpp_ultra_rest", out->transport, sizeof(out->transport));
            return 1;
        }

        out->executed = 1;
        copy_to_buffer(
            extract_json_string(response.body, "orderId").value_or(""),
            out->order_id,
            sizeof(out->order_id)
        );
        copy_to_buffer("cpp_ultra_rest", out->transport, sizeof(out->transport));
        return 1;
    }

private:
    bool refresh_symbols() {
        std::unordered_set<std::string> next_symbols;
        std::string cursor;
        do {
            std::string path = "/v5/market/instruments-info?category=spot&limit=1000";
            if (!cursor.empty()) {
                path += "&cursor=" + client_.escape(cursor);
            }
            const auto response = client_.get(path);
            if (!response.success) {
                return false;
            }
            const auto symbols = extract_symbols(response.body);
            for (const auto& symbol : symbols) {
                next_symbols.insert(symbol);
            }
            cursor = extract_json_string(response.body, "nextPageCursor").value_or("");
        } while (!cursor.empty());
        if (!next_symbols.empty()) {
            spot_symbols_ = std::move(next_symbols);
        }
        return !spot_symbols_.empty();
    }

    bool has_spot_symbol(const std::string& symbol) {
        if (spot_symbols_.find(symbol) != spot_symbols_.end()) {
            return true;
        }
        if (cache_only_symbol_check_) {
            return false;
        }
        refresh_symbols();
        return spot_symbols_.find(symbol) != spot_symbols_.end();
    }

    std::vector<std::string> auth_headers(const std::string& body) {
        const std::string timestamp = now_ms();
        const std::string plain = timestamp + api_key_ + recv_window_ + body;
        const std::string signature = sign(plain);
        return {
            "Content-Type: application/json",
            "X-BAPI-API-KEY: " + api_key_,
            "X-BAPI-SIGN: " + signature,
            "X-BAPI-TIMESTAMP: " + timestamp,
            "X-BAPI-RECV-WINDOW: " + recv_window_,
        };
    }

    std::string sign(const std::string& payload) const {
        unsigned char digest[EVP_MAX_MD_SIZE];
        unsigned int digest_len = 0;
        HMAC(
            EVP_sha256(),
            api_secret_.data(),
            static_cast<int>(api_secret_.size()),
            reinterpret_cast<const unsigned char*>(payload.data()),
            payload.size(),
            digest,
            &digest_len
        );
        std::ostringstream hex;
        hex << std::hex << std::setfill('0');
        for (unsigned int i = 0; i < digest_len; ++i) {
            hex << std::setw(2) << static_cast<int>(digest[i]);
        }
        return hex.str();
    }

    static std::string now_ms() {
        const auto now = std::chrono::time_point_cast<std::chrono::milliseconds>(
            std::chrono::system_clock::now()
        );
        return std::to_string(now.time_since_epoch().count());
    }

    std::string api_key_;
    std::string api_secret_;
    std::string base_url_;
    std::string recv_window_;
    bool buy_enabled_{false};
    std::string buy_quote_amount_;
    bool cache_only_symbol_check_{true};
    CurlClient client_;
    std::unordered_set<std::string> spot_symbols_;
    std::unordered_set<std::string> seen_keys_;
    std::mutex mu_;
};

ListingUltraEngine& global_engine() {
    static ListingUltraEngine engine;
    return engine;
}

}  // namespace

extern "C" int listing_ultra_warmup() {
    return global_engine().warmup();
}

extern "C" int handle_listing_post(
    const char* exchange,
    long long message_id,
    const char* title,
    NativeUltraResult* out
) {
    if (exchange == nullptr || title == nullptr || out == nullptr) {
        return -1;
    }
    return global_engine().handle(exchange, message_id, title, out);
}
