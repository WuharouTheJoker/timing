import math

class RCTree:
    def __init__(self, r_unit=1.0, c_unit=1.0):
        self.name = ''
        self.graph = {}
        self.resistance = {}
        self.node_self_cap = {}
        self.r_unit = r_unit
        self.c_unit = c_unit

    def set_name(self,name):
        self.name = name

    def add_edge(self, node1, node2, res):
        res = res * self.r_unit
        self.graph.setdefault(node1, []).append(node2)
        self.graph.setdefault(node2, []).append(node1)
        self.resistance[(node1, node2)] = res
        self.resistance[(node2, node1)] = res

    def set_node_cap(self, node, cap):
        cap = cap * self.c_unit
        self.node_self_cap[node] = cap


    def compute_delays_to_loads(self, driver, loads, apply_ln2=False):
        """
        针对一个driver节点，遍历RC树，
        同时记录每个load路径和节点的下游电容，
        最后计算所有load的Elmore延迟。
        """
        subtree_cap = {}
        parent = {}
        path_to = {}
        visited = set()

        stack = [(driver, None)]
        postorder = []

        # DFS，建立 parent 和 path_to，同时记录遍历顺序
        while stack:
            node, par = stack.pop()
            if node in visited:
                continue
            visited.add(node)
            parent[node] = par
            if par is None:
                path_to[node] = [node]
            else:
                path_to[node] = path_to[par] + [node]
            postorder.append(node)
            for neighbor in self.graph.get(node, []):
                if neighbor != par:
                    stack.append((neighbor, node))

        # 反向遍历，计算每个节点的子树电容
        for node in reversed(postorder):
            cap = self.node_self_cap.get(node, 0.0)
            for neighbor in self.graph.get(node, []):
                if parent.get(neighbor) == node:
                    cap += subtree_cap.get(neighbor, 0.0)
            subtree_cap[node] = cap

        # 计算从 driver 到每个 load 的延迟
        delays = {}
        for load in loads:
            if load not in path_to:
                delays[load] = None
                continue
            path = path_to[load]
            delay = 0.0
            for i in range(len(path) - 1):
                u, v = path[i], path[i + 1]
                r = self.resistance.get((u, v), 0.0)
                delay += r * subtree_cap[v]
            if apply_ln2:
                delay *= math.log(2)
            delays[load] = delay*1e-6

        return delays
    
import numpy as np

class RCTreeM:
    def __init__(self, r_unit=1.0, c_unit=1.0):
        self.name = ''
        self.node_index = {}         # 节点名 -> 索引
        self.index_node = []         # 索引 -> 节点名
        self.adj_matrix = None       # 邻接矩阵 (电阻)
        self.cap_array = None        # 电容数组
        self.r_unit = r_unit
        self.c_unit = c_unit
        self.edge_list = []          # 边列表

    def _ensure_node(self, node):
        """确保节点存在并分配索引"""
        if node not in self.node_index:
            idx = len(self.index_node)
            self.node_index[node] = idx
            self.index_node.append(node)

    def set_name(self, name):
        self.name = name

    def add_edge(self, node1, node2, res):
        self._ensure_node(node1)
        self._ensure_node(node2)
        idx1 = self.node_index[node1]
        idx2 = self.node_index[node2]
        res *= self.r_unit
        self.edge_list.append((idx1, idx2, res))

    def set_node_cap(self, node, cap):
        self._ensure_node(node)
        idx = self.node_index[node]
        cap *= self.c_unit
        if self.cap_array is None or len(self.cap_array) <= idx:
            new_size = max(idx + 1, len(self.cap_array) if self.cap_array is not None else 0)
            new_cap = np.zeros(new_size)
            if self.cap_array is not None:
                new_cap[:len(self.cap_array)] = self.cap_array
            self.cap_array = new_cap
        self.cap_array[idx] = cap

    def _build_matrices(self):
        n = len(self.index_node)
        self.adj_matrix = np.zeros((n, n))
        for i, j, r in self.edge_list:
            self.adj_matrix[i, j] = r
            self.adj_matrix[j, i] = r
        if self.cap_array is None:
            self.cap_array = np.zeros(n)
        elif len(self.cap_array) < n:
            # 补足未设置电容的节点
            new_cap = np.zeros(n)
            new_cap[:len(self.cap_array)] = self.cap_array
            self.cap_array = new_cap


    def compute_delays_to_loads(self, driver, loads, apply_ln2=False):
        self._build_matrices()

        # 如果是名字（字符串），则转换为索引
        if isinstance(driver, str):
            if driver not in self.node_index:
                return {load: None for load in loads}
            driver_idx = self.node_index[driver]
        else:
            driver_idx = driver

        load_indices = []
        for load in loads:
            if isinstance(load, str):
                if load not in self.node_index:
                    load_indices.append(None)
                else:
                    load_indices.append(self.node_index[load])
            else:
                load_indices.append(load)

        n = len(self.index_node)
        visited = np.zeros(n, dtype=bool)
        parent = np.full(n, -1, dtype=int)
        subtree_cap = np.zeros(n)
        stack = [driver_idx]
        postorder = []

        # DFS to build parent and postorder
        while stack:
            node = stack.pop()
            if visited[node]:
                continue
            visited[node] = True
            postorder.append(node)
            for neighbor in np.nonzero(self.adj_matrix[node])[0]:
                if not visited[neighbor]:
                    parent[neighbor] = node
                    stack.append(neighbor)

        # Bottom-up cap accumulation
        for node in reversed(postorder):
            total_cap = self.cap_array[node]
            children = np.where(parent == node)[0]
            for child in children:
                total_cap += subtree_cap[child]
            subtree_cap[node] = total_cap

        # Delay calculation
        delays = {}
        for load, load_idx in zip(loads, load_indices):
            if load_idx is None:
                delays[load] = None
                continue
            delay = 0.0
            current = load_idx
            while current != driver_idx and current != -1:
                par = parent[current]
                r = self.adj_matrix[par, current]
                delay += r * subtree_cap[current]
                current = par
            if apply_ln2:
                delay *= np.log(2)
            delays[load] = delay * 1e-6
        return delays
