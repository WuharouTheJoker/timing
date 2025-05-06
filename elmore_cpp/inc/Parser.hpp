#ifndef PARSER_HPP
#define PARSER_HPP

#include <string>
#include <unordered_map>
#include <vector>

class Parser {
public:
    // Net 对应的 IO 信息结构体
    struct NetIO {
        std::vector<std::string> output;
        std::vector<std::string> inputs;
    };

    // 解析 netlist_info.txt
    static std::unordered_map<std::string, NetIO> parse_netlist_info(const std::string& filepath);

    // 解析 SPEF 文件中的 *NAME_MAP
    static std::unordered_map<std::string, std::string> parse_name_map(const std::string& spef_path);

    static std::vector<std::string> split(const std::string& str, char delimiter);

};

#endif // PARSER_HPP
