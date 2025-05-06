#include "Parser.hpp"
#include <fstream>
#include <sstream>
#include <regex>
#include <iostream>

std::unordered_map<std::string, Parser::NetIO> Parser::parse_netlist_info(const std::string& filepath) {
    std::unordered_map<std::string, NetIO> net_to_io;
    std::ifstream file(filepath);
    std::string line;
    std::string current_net;

    if (!file.is_open()) {
        std::cerr << "Failed to open netlist file: " << filepath << std::endl;
        return net_to_io;
    }

    while (std::getline(file, line)) {
        line.erase(0, line.find_first_not_of(" \t")); // trim left

        if (line.find("Net name:") == 0) {
            std::smatch match;
            std::regex re(R"(\{(.+?)\})");
            if (std::regex_search(line, match, re)) {
                current_net = match[1];
            } else {
                size_t pos = line.find(":");
                current_net = line.substr(pos + 1);
                current_net.erase(0, current_net.find_first_not_of(" \t")); // trim
            }
            net_to_io[current_net] = NetIO{};
        }

        else if (line.find("Output") == 0 && !current_net.empty()) {
            size_t pos = line.find(":");
            std::string output = line.substr(pos + 1);
            output.erase(0, output.find_first_not_of(" \t")); // trim left

            size_t space_pos = output.find(" ");
            if (space_pos != std::string::npos) {
                output = output.substr(0, space_pos); // remove "(CELLTYPE)"
            }

            net_to_io[current_net].output.push_back(output);
        }

        else if (line.find("Input") == 0 && !current_net.empty()) {
            size_t pos = line.find(":");
            std::string input = line.substr(pos + 1);
            input.erase(0, input.find_first_not_of(" \t")); // trim left

            size_t space_pos = input.find(" ");
            if (space_pos != std::string::npos) {
                input = input.substr(0, space_pos); // remove "(CELLTYPE)"
            }

            net_to_io[current_net].inputs.push_back(input);
        }
    }

    return net_to_io;
}


std::unordered_map<std::string, std::string> Parser::parse_name_map(const std::string& spef_path) {
    std::unordered_map<std::string, std::string> name_map;
    std::ifstream file(spef_path);
    std::string line;
    bool in_name_map = false;
    std::regex pattern(R"(\*(\d+)\s+(\S+))");

    if (!file.is_open()) {
        std::cerr << "Failed to open SPEF file: " << spef_path << std::endl;
        return name_map;
    }

    while (std::getline(file, line)) {
        line.erase(0, line.find_first_not_of(" \t")); // trim left

        if (line.find("*NAME_MAP") == 0) {
            in_name_map = true;
            continue;
        }

        if (in_name_map) {
            if (line.empty() || line[0] != '*') break;

            std::smatch match;
            if (std::regex_match(line, match, pattern)) {
                name_map[match[1]] = match[2];
            } else {
                break; // 非 *数字 name 格式，认为 name map 结束
            }
        }
    }

    return name_map;
}

std::vector<std::string> Parser::split(const std::string& str, char delimiter) {
    std::vector<std::string> tokens;
    std::stringstream ss(str);
    std::string tok;
    while (std::getline(ss, tok, delimiter)) {
        if (!tok.empty()) tokens.push_back(tok);
    }
    return tokens;
}
