#ifndef RCTREE_HPP
#define RCTREE_HPP

#include <unordered_map>
#include <unordered_set>
#include <vector>
#include <string>
#include <cmath>

class RCTree {
public:
    RCTree(double r_unit = 1.0, double c_unit = 1.0);
    void set_name(const std::string& name);
    void add_edge(const std::string& node1, const std::string& node2, double res);
    void set_node_cap(const std::string& node, double cap);
    std::unordered_map<std::string, double> compute_delays_to_loads(const std::string& driver,
        const std::vector<std::string>& loads, bool apply_ln2 = false) const;
    std::string name;
private:

    double r_unit;
    double c_unit;

    std::unordered_map<std::string, std::vector<std::string>> graph;
    std::unordered_map<std::string, double> node_self_cap;
    std::unordered_map<std::string, double> resistance; // key: node1 + "," + node2

    std::string edge_key(const std::string& u, const std::string& v) const;
};

#endif // RCTREE_HPP
