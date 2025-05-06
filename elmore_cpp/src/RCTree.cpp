#include "RCTree.hpp"
#include <stack>
#include <algorithm>

RCTree::RCTree(double r_unit, double c_unit) : r_unit(r_unit), c_unit(c_unit) {}

void RCTree::set_name(const std::string& name) {
    this->name = name;
}

void RCTree::add_edge(const std::string& node1, const std::string& node2, double res) {
    res *= r_unit;
    graph[node1].push_back(node2);
    graph[node2].push_back(node1);
    resistance[edge_key(node1, node2)] = res;
    resistance[edge_key(node2, node1)] = res;
}

void RCTree::set_node_cap(const std::string& node, double cap) {
    node_self_cap[node] = cap * c_unit;
}

std::unordered_map<std::string, double> RCTree::compute_delays_to_loads(
    const std::string& driver,
    const std::vector<std::string>& loads,
    bool apply_ln2) const {

    std::unordered_map<std::string, double> subtree_cap;
    std::unordered_map<std::string, std::string> parent;
    std::unordered_map<std::string, std::vector<std::string>> path_to;
    std::unordered_set<std::string> visited;
    std::vector<std::string> postorder;

    std::stack<std::pair<std::string, std::string>> stack;
    stack.push({driver, ""});

    while (!stack.empty()) {
        auto [node, par] = stack.top();
        stack.pop();
        if (visited.count(node)) continue;
        visited.insert(node);
        parent[node] = par;
        if (par.empty()) path_to[node] = {node};
        else {
            path_to[node] = path_to[par];
            path_to[node].push_back(node);
        }
        postorder.push_back(node);
        for (const auto& neighbor : graph.at(node)) {
            if (neighbor != par)
                stack.push({neighbor, node});
        }
    }

    for (auto it = postorder.rbegin(); it != postorder.rend(); ++it) {
        const auto& node = *it;
        double cap = node_self_cap.count(node) ? node_self_cap.at(node) : 0.0;
        for (const auto& neighbor : graph.at(node)) {
            if (parent.count(neighbor) && parent.at(neighbor) == node) {
                cap += subtree_cap[neighbor];
            }
        }
        subtree_cap[node] = cap;
    }

    std::unordered_map<std::string, double> delays;
    for (const auto& load : loads) {
        if (!path_to.count(load)) {
            delays[load] = -1.0;
            continue;
        }
        const auto& path = path_to[load];
        double delay = 0.0;
        for (size_t i = 0; i + 1 < path.size(); ++i) {
            std::string u = path[i], v = path[i + 1];
            double r = resistance.count(edge_key(u, v)) ? resistance.at(edge_key(u, v)) : 0.0;
            delay += r * subtree_cap.at(v);
        }
        if (apply_ln2)
            delay *= std::log(2.0);
        delays[load] = delay * 1e-6;
    }
    return delays;
}

std::string RCTree::edge_key(const std::string& u, const std::string& v) const {
    return u + "," + v;
}
