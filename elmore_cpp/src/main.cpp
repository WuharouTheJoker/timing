#include <iostream>
#include <fstream>
#include <string>
#include <unordered_map>
#include <vector>
#include <chrono>
#include <filesystem>
#include <iomanip>
#include "Parser.hpp"
#include "RCTree.hpp"

namespace fs = std::filesystem;

void compute_and_save_delays(
    const std::string& spef_path,
    const std::string& netlist_path,
    const std::string& output_dir
) {
    auto net_info = Parser::parse_netlist_info(netlist_path);
    auto name_map = Parser::parse_name_map(spef_path);
    std::ifstream spef_file(spef_path);
    std::string line;

    if (!spef_file.is_open()) {
        std::cerr << "Failed to open SPEF file: " << spef_path << std::endl;
        return;
    }

    int dnet_count = 0;
    std::unordered_map<std::string, std::string> raw_to_real_name;
    RCTree rctree;
    bool in_dnet = false, in_conn = false, in_cap = false, in_res = false;

    if (!fs::exists(output_dir)) {
        fs::create_directories(output_dir);
    }

    std::string base_filename = fs::path(spef_path).stem().string();
    std::string output_file = (fs::path(output_dir) / (base_filename + ".txt")).string();
    std::ofstream output_txt(output_file);

    while (std::getline(spef_file, line)) {
        line.erase(0, line.find_first_not_of(" \t"));
        if (line.rfind("*D_NET", 0) == 0 && !in_dnet) {
            dnet_count++;
            in_dnet = true;
            raw_to_real_name.clear();
            rctree = RCTree();  // 重建对象，清空原有状态
            auto parts = Parser::split(line, ' ');
            std::string net_id = parts[1];
            if (net_id[0] == '*') net_id = net_id.substr(1);
            std::string net_name = name_map.count(net_id) ? name_map[net_id] : net_id;
            rctree.set_name(net_name);
            continue;
        }

        if (in_dnet && line.rfind("*END", 0) == 0) {
            in_dnet = false;

            if (net_info.count(rctree.name)) {
                const auto& info = net_info[rctree.name];
                std::unordered_map<std::string, std::string> reverse_map;
                for (const auto& [k, v] : raw_to_real_name) reverse_map[v] = k;

                for (const auto& input_name : info.inputs) {
                    auto it = reverse_map.find(input_name);
                    if (it == reverse_map.end()) {
                        std::cerr << "⚠️ 未找到输入节点 " << input_name << " 的编号\n";
                        continue;
                    }
                    std::string input_node = it->second;

                    std::vector<std::string> load_nodes, load_names;
                    for (const auto& output_name : info.output) {
                        auto oit = reverse_map.find(output_name);
                        if (oit != reverse_map.end()) {
                            load_nodes.push_back(oit->second);
                            load_names.push_back(output_name);
                        } else {
                            std::cerr << "⚠️ 未找到输出节点 " << output_name << " 的编号\n";
                        }
                    }

                    if (!load_nodes.empty()) {
                        auto delays = rctree.compute_delays_to_loads(input_node, load_nodes);
                        for (size_t i = 0; i < load_nodes.size(); ++i) {
                            output_txt << load_names[i] << " " << input_name << " "
                                       << std::fixed << std::setprecision(6)
                                       << delays[load_nodes[i]] << "\n";
                        }
                    }
                }
            } else {
                std::cerr << "⚠️ net_info 中未找到 RC 树名称 " << rctree.name << "\n";
            }
            continue;
        }

        if (in_dnet) {
            if (line.rfind("*CONN", 0) == 0) { in_conn = true; in_cap = false; in_res = false; continue; }
            if (line.rfind("*CAP", 0) == 0)  { in_conn = false; in_cap = true; in_res = false; continue; }
            if (line.rfind("*RES", 0) == 0)  { in_conn = false; in_cap = false; in_res = true; continue; }

            if (in_conn && line.rfind("*I", 0) == 0) {
                auto parts = Parser::split(line, ' ');
                if (parts.size() >= 3) {
                    std::string raw_node = parts[1];
                    if (raw_node[0] == '*') raw_node = raw_node.substr(1);
                    auto pos = raw_node.find(':');
                    if (pos != std::string::npos) {
                        std::string name_id = raw_node.substr(0, pos);
                        std::string port = raw_node.substr(pos + 1);
                        if (name_map.count(name_id)) {
                            raw_to_real_name[raw_node] = name_map[name_id] + "/" + port;
                        }
                    }
                }
            } else if (in_cap) {
                auto parts = Parser::split(line, ' ');
                if (parts.size() >= 3) {
                    std::string node = parts[1];
                    if (node[0] == '*') node = node.substr(1);
                    rctree.set_node_cap(node, std::stod(parts[2]));
                }
            } else if (in_res) {
                auto parts = Parser::split(line, ' ');
                if (parts.size() >= 4) {
                    std::string node1 = parts[1];
                    std::string node2 = parts[2];
                    if (node1[0] == '*') node1 = node1.substr(1);
                    if (node2[0] == '*') node2 = node2.substr(1);
                    rctree.add_edge(node1, node2, std::stod(parts[3]));
                }
            }
        }
    }

    std::cout << "D_NET总数: " << dnet_count << "\n";
    
    std::cout << "✅ 时延计算结果已保存到 " << output_file << "\n";
}

int main(int argc, char* argv[]) {
    if (argc != 4) {
        std::cerr << "Usage: " << argv[0] << " <netlist> <spef> <output_dir>\n";
        return 1;
    }

    std::string netlist_path = argv[1];
    std::string spef_path = argv[2];
    std::string output_dir = argv[3];

    auto start = std::chrono::high_resolution_clock::now();
    compute_and_save_delays(spef_path, netlist_path, output_dir);
    auto end = std::chrono::high_resolution_clock::now();

    std::chrono::duration<double> elapsed = end - start;
    std::cout << "代码执行时间: " << std::fixed << std::setprecision(6) << elapsed.count() << " 秒\n";

    return 0;
}
