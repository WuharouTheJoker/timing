import os
import re
from collections import defaultdict
import json

def parse_netlist_info(netlist_path): 
    net_to_io = {}
    current_net = None

    with open(netlist_path, 'r') as f:
        for line in f:
            line = line.strip()
            
            # 解析 Net name
            if line.startswith("Net name:"):
                match = re.search(r'\{(.+?)\}', line)
                if match:  # 如果是大括号形式，提取大括号内的内容
                    current_net = match.group(1)
                else:  # 如果没有大括号，直接取后面的内容
                    current_net = line.split(":")[1].strip()

                net_to_io[current_net] = {"output": [], "inputs": []}

            # 解析 Output 节点
            elif line.startswith("Output") and current_net:
                full_path = line.split(":")[1].strip().split()[0]
                net_to_io[current_net]["output"].append(full_path)

            # 解析 Input 节点
            elif line.startswith("Input") and current_net:
                full_path = line.split(":")[1].strip().split()[0]
                net_to_io[current_net]["inputs"].append(full_path)

    return net_to_io



def parse_name_map(spef_path):
    name_map = {}
    in_name_map = False
    pattern = re.compile(r'\*(\d+)\s+(\S+)')

    with open(spef_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('*NAME_MAP'):
                in_name_map = True
                continue

            if in_name_map:
                if not line.startswith('*'):
                    break  # 到达非 * 开头的行，说明 name map 结束
                match = pattern.match(line)
                if match:
                    idx, name = match.groups()
                    name_map[idx] = name
                else:
                    break  # 不再是 *数字 name 的格式，name map 结束

    return name_map

def spef_to_dgl_json(spef_path, output_dir):
    with open(spef_path, 'r') as f:
        current_net = None
        in_cap_block = False
        in_res_block = False
        in_conn_block = False

        for line in f:
            line = line.strip()

            if line.startswith('*D_NET'):
                if current_net is not None:
                    # 已经处理过一个 D_NET，停止处理
                    break

                net_id = line.split()[1].lstrip('*')
                current_net = {
                    "id": net_id,
                    "nodes": {},
                    "edges": [],
                    "inputs": [],
                    "output": None
                }
                in_cap_block = False
                in_res_block = False
                in_conn_block = False

            elif current_net is not None and line.startswith('*CAP'):
                in_cap_block = True
                in_res_block = False
                in_conn_block = False

            elif current_net is not None and line.startswith('*RES'):
                in_cap_block = False
                in_res_block = True
                in_conn_block = False

            elif current_net is not None and line.startswith('*CONN'):
                in_cap_block = False
                in_res_block = False
                in_conn_block = True

            elif current_net is not None and (line.startswith('*END') or line.startswith('*D_NET')):
                break

            elif current_net is not None and in_conn_block and line.startswith('*I'):
                parts = line.split()
                if len(parts) >= 3:
                    node_name = parts[1].lstrip('*')
                    direction = parts[2]
                    if direction == 'I':
                        current_net["inputs"].append(node_name)
                    elif direction == 'O':
                        current_net["output"] = node_name

            elif current_net is not None and in_cap_block:
                parts = line.split()
                if len(parts) == 3:
                    node = parts[1].lstrip('*')
                    cap = float(parts[2])
                    if node not in current_net["nodes"]:
                        current_net["nodes"][node] = {
                            "id": node,
                            "capacitance": cap
                        }
                    else:
                        current_net["nodes"][node]["capacitance"] = cap

            elif current_net is not None and in_res_block:
                parts = line.split()
                if len(parts) == 4:
                    node1 = parts[1].lstrip('*')
                    node2 = parts[2].lstrip('*')
                    res = float(parts[3])

                    for node in [node1, node2]:
                        if node not in current_net["nodes"]:
                            current_net["nodes"][node] = {
                                "id": node,
                                "capacitance": 0.0
                            }

                    current_net["edges"].append({
                        "source": node1,
                        "target": node2,
                        "resistance": res
                    })

    # 保存 JSON
    if current_net:
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{current_net['id']}.json")
        with open(output_path, 'w') as f:
            json.dump(current_net, f, indent=4)
        print(f"已保存 {output_path}")
    else:
        print("未能解析到任何 *D_NET 内容")

# 使用示例
spef_path = 'timing/RC-GNN/Data/SPEF/Group0.spef'
netlist_path = 'timing/RC-GNN/Data/netlist_info.txt'
output_dir = 'timing/RC-GNN/datasets'
spef_to_dgl_json(spef_path, output_dir)