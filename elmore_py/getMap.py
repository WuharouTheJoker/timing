import os
import re
from collections import defaultdict
from RCTree import *  


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








    