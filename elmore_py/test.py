from RCTree import *  # 或 RCTreeOptimized
tree = RCTree()

tree.set_node_cap('1', 0.5)
tree.set_node_cap('2', 1.0)
tree.set_node_cap('3', 2.0)
tree.set_node_cap('4', 4.0)

# 添加边
tree.add_edge('1', '2', 1)
tree.add_edge('1', '3', 2)
tree.add_edge('3', '4', 3)

# 添加节点电容

# 计算延迟
delays = tree.compute_delays_to_loads(driver='1', loads=['2', '4'], apply_ln2=False)
print(delays)
print(tree.graph)