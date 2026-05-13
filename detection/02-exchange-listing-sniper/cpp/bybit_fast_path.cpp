#include <curl/curl.h>
#include <openssl/hmac.h>

#include <atomic>
#include <chrono>
#include <cctype>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <iomanip>
#include <iostream>
#include <mutex>
#include <optional>
#include <sstream>
#include <string>
#include <thread>
#include <unordered_set>
#include <vector>

namespace {

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

std::vector<std::string> split_tab_line(const std::string& line) {
    std::vector<std::string> parts;
    size_t start = 0;
    while (start <= line.size()) {
        size_t end = line.find('\t', start);
        if (end == std::string::npos) {
            parts.push_back(line.substr(start));
            break;
        }
        parts.push_back(line.substr(start, end - start));
        start = end + 1;
    }
    return parts;
}

bool read_frame(std::istream& input, std::string& out) {
    unsigned char header[4];
    if (!input.read(reinterpret_cast<char*>(header), sizeof(header))) {
        return false;
    }
    const std::uint32_t size =
        (static_cast<std::uint32_t>(header[0]) << 24) |
        (static_cast<std::uint32_t>(header[1]) << 16) |
        (static_cast<std::uint32_t>(header[2]) << 8) |
        static_cast<std::uint32_t>(header[3]);
    out.resize(size);
    if (size == 0) {
        return true;
    }
    return static_cast<bool>(input.read(out.data(), static_cast<std::streamsize>(size)));
}

void write_frame(std::ostream& output, const std::string& payload) {
    const std::uint32_t size = static_cast<std::uint32_t>(payload.size());
    const unsigned char header[4] = {
        static_cast<unsigned char>((size >> 24) & 0xff),
        static_cast<unsigned char>((size >> 16) & 0xff),
        static_cast<unsigned char>((size >> 8) & 0xff),
        static_cast<unsigned char>(size & 0xff),
    };
    output.write(reinterpret_cast<const char*>(header), sizeof(header));
    if (!payload.empty()) {
        output.write(payload.data(), static_cast<std::streamsize>(payload.size()));
    }
    output.flush();
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

    HttpResult post(
        const std::string& path,
        const std::string& body,
        const std::vector<std::string>& headers = {}
    ) {
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
    HttpResult perform(
        const std::string& method,
        const std::string& path,
        const std::string& body,
        const std::vector<std::string>& headers
    ) {
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
        curl_easy_setopt(curl_, CURLOPT_USERAGENT, "ChainPulse-FastPath/1.0");

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

class BybitFastPath {
public:
    BybitFastPath()
        : api_key_(getenv_or("BYBIT_API_KEY")),
          api_secret_(getenv_or("BYBIT_API_SECRET")),
          base_url_(getenv_or("BYBIT_API_BASE_URL", "https://api.bybit.com")),
          recv_window_(getenv_or("BYBIT_RECV_WINDOW", "5000")),
          client_(base_url_) {}

    bool self_test() {
        const std::string signature = sign("1700000000000testkey5000{}");
        if (signature.size() != 64) {
            std::cerr << "self-test failed: bad signature length\n";
            return false;
        }
        const auto response = make_success("VVVUSDT", "order-1", 0, "ok");
        return response.rfind("BUY\t1\t1\tVVVUSDT\torder-1\t0\tok\t", 0) == 0;
    }

    bool warmup() {
        schedule_refresh();
        return true;
    }

    int run_server() {
        warmup();
        std::string frame;
        while (read_frame(std::cin, frame)) {
            write_frame(std::cout, handle_command(frame));
        }
        return 0;
    }

private:
    std::string handle_command(const std::string& line) {
        const auto parts = split_tab_line(line);
        if (parts.empty()) {
            return make_error("invalid_command");
        }
        if (parts[0] == "PING") {
            return "PONG";
        }
        if (parts[0] == "REFRESH") {
            const bool ok = refresh_symbols();
            return std::string("REFRESH\t") + (ok ? "1" : "0") +
                   "\t" + std::to_string(spot_symbol_count());
        }
        if (parts[0] == "BUY") {
            if (parts.size() != 4) {
                return make_error("buy_command_requires_3_args");
            }
            return place_market_buy_quote(parts[1], parts[2], parts[3]);
        }
        if (parts[0] == "HAS") {
            if (parts.size() != 2) {
                return make_error("has_command_requires_symbol");
            }
            if (!has_spot_symbol(parts[1])) {
                schedule_refresh();
                return "HAS\t0";
            }
            return std::string("HAS\t") +
                   "1";
        }
        return make_error("unknown_command");
    }

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
            const auto next_cursor = extract_json_string(response.body, "nextPageCursor");
            cursor = next_cursor.value_or("");
        } while (!cursor.empty());

        if (!next_symbols.empty()) {
            std::lock_guard<std::mutex> lock(spot_symbols_mu_);
            spot_symbols_ = std::move(next_symbols);
        }
        return spot_symbol_count() > 0;
    }

    bool has_spot_symbol(const std::string& symbol) {
        std::lock_guard<std::mutex> lock(spot_symbols_mu_);
        return spot_symbols_.find(symbol) != spot_symbols_.end();
    }

    std::size_t spot_symbol_count() {
        std::lock_guard<std::mutex> lock(spot_symbols_mu_);
        return spot_symbols_.size();
    }

    void schedule_refresh() {
        bool expected = false;
        if (!refresh_in_flight_.compare_exchange_strong(expected, true)) {
            return;
        }
        std::thread([this]() {
            refresh_symbols();
            refresh_in_flight_.store(false);
        }).detach();
    }

    std::string place_market_buy_quote(
        const std::string& symbol,
        const std::string& quote_amount,
        const std::string& order_link_id
    ) {
        if (api_key_.empty() || api_secret_.empty()) {
            return make_error("missing_api_config", symbol);
        }

        const std::string body =
            "{\"category\":\"spot\",\"symbol\":\"" + symbol +
            "\",\"side\":\"Buy\",\"orderType\":\"Market\",\"qty\":\"" + quote_amount +
            "\",\"orderFilter\":\"Order\",\"marketUnit\":\"quoteCoin\",\"orderLinkId\":\"" +
            order_link_id + "\"}";

        const auto response = client_.post(
            "/v5/order/create",
            body,
            auth_headers(body)
        );
        const long long ret_code = extract_json_int(response.body, "retCode").value_or(-1);
        if (!response.success || ret_code != 0) {
            const std::string reason =
                extract_json_string(response.body, "retMsg").value_or(
                    response.error.empty() ? "order_create_failed" : response.error
                );
            return make_error(reason, symbol, true, static_cast<int>(ret_code));
        }

        const std::string order_id =
            extract_json_string(response.body, "orderId").value_or("");
        return make_success(symbol, order_id, static_cast<int>(ret_code), "cpp_fast_path");
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

    static std::string make_error(
        const std::string& reason,
        const std::string& symbol = "",
        bool attempted = false,
        int ret_code = -1
    ) {
        std::string out = "BUY\t0\t";
        out += attempted ? "1\t" : "0\t";
        out += symbol;
        out += "\t\t";
        out += std::to_string(ret_code);
        out += "\tcpp_fast_path\t";
        out += json_escape(reason);
        return out;
    }

    static std::string make_success(
        const std::string& symbol,
        const std::string& order_id,
        int ret_code,
        const std::string& transport
    ) {
        std::string out = "BUY\t1\t1\t";
        out += symbol;
        out += "\t";
        out += order_id;
        out += "\t";
        out += std::to_string(ret_code);
        out += "\t";
        out += transport;
        out += "\t";
        return out;
    }

    std::string api_key_;
    std::string api_secret_;
    std::string base_url_;
    std::string recv_window_;
    CurlClient client_;
    std::atomic<bool> refresh_in_flight_{false};
    std::mutex spot_symbols_mu_;
    std::unordered_set<std::string> spot_symbols_;
};

}  // namespace

int main(int argc, char** argv) {
    BybitFastPath fast_path;

    if (argc > 1 && std::string(argv[1]) == "--self-test") {
        const bool ok = fast_path.self_test();
        std::cout << (ok ? "SELFTEST_OK" : "SELFTEST_FAIL") << '\n';
        return ok ? 0 : 1;
    }

    if (argc > 1 && std::string(argv[1]) == "--server") {
        return fast_path.run_server();
    }

    std::cerr << "usage: bybit_fast_path --server | --self-test\n";
    return 1;
}
