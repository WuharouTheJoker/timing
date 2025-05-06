from getMap import *
from RCTree import *
import argparse
import os
import time
from evaluate import *

def compute_and_save_delays(spef_path, output_dir):

    name_map = parse_name_map(spef_path)
    count = 0
    with open(spef_path, 'r') as spef_file:
        lines = spef_file.readlines()
    
    raw_to_real_name = {}
    rctree = None
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    spef_filename = os.path.basename(spef_path)
    base_filename = os.path.splitext(spef_filename)[0]
    output_file = os.path.join(output_dir, f"{base_filename}.txt")
    input_nodes = []
    output_nodes = []
    with open(output_file, 'w') as output_txt:
        in_dnet = False
        in_conn = False
        in_cap = False
        in_res = False

        for line in lines:
            line = line.strip()
            
            if line.startswith("*D_NET") and not in_dnet:
                count+=1
                in_dnet = True
                raw_to_real_name = {}
                rctree = RCTree()
                input_nodes = []
                output_nodes = []
                
                parts = line.split()
                net_id = parts[1].lstrip("*")
                net_name = name_map.get(net_id, net_id)
                rctree.set_name(net_name)
                continue
            
            if in_dnet and line.startswith("*END"):

                in_dnet = False
               

                for input_node in input_nodes:
                    input_name = raw_to_real_name.get(input_node)
                    delays = rctree.compute_delays_to_loads(input_node, output_nodes)

                    for load_node, delay in delays.items():
                        load_real_name = raw_to_real_name.get(load_node)
                        output_txt.write(f"{load_real_name} {input_name} {delay:.6f}\n")

            
            if in_dnet:
                if line.startswith("*CONN"):
                    in_conn = True
                    in_cap = False
                    in_res = False
                    continue
                elif line.startswith("*CAP"):
                    in_conn = False
                    in_cap = True
                    in_res = False
                    continue
                elif line.startswith("*RES"):
                    in_conn = False
                    in_cap = False
                    in_res = True
                    continue

            if in_conn and line.startswith("*I"):
                parts = line.split()
                if len(parts) >= 3:
                    raw_node = parts[1].lstrip('*')
                    if ':' in raw_node:
                        name_id, port = raw_node.split(':')
                        mapped = name_map.get(name_id)
                        if mapped:
                            raw_to_real_name[raw_node] = f"{mapped}/{port}"

                    node_id = parts[1].lstrip('*')  # 获取纯编号，例如 "12"
                    direction = parts[2]  # I 或 O
                    if direction == 'I':
                        input_nodes.append(node_id)
                    elif direction == 'O':
                        output_nodes.append(node_id)


            elif in_cap:
                parts = line.split()
                if len(parts) >= 3:
                    node = parts[1].lstrip('*')
                    cap = float(parts[2])
                    rctree.set_node_cap(node, cap)

            elif in_res:
                parts = line.split()
                if len(parts) >= 4:
                    node1 = parts[1].lstrip('*')
                    node2 = parts[2].lstrip('*')
                    res = float(parts[3])
                    rctree.add_edge(node1, node2, res)
    print(f"D_NET总数 {count}")
    print(f"✅ 时延计算结果已保存到 {output_file}")
    return output_file

"Data/netlist_info.txt"
"Data/SPEF/Group0.spef"
"Data/SPEF/Group1.spef"
"Data/my_delay"

def parse_args():
    parser = argparse.ArgumentParser(description="计算时延并保存结果")
    
    # 添加命令行参数
    parser.add_argument('--spef', type=str, required=True, help="SPEF 文件路径")
    parser.add_argument('--output', type=str, required=True, help="输出目录路径")
    parser.add_argument('--golden', type=str, required=True)

    return parser.parse_args()

if __name__ == "__main__":
    # 解析命令行参数
    args = parse_args()

    # 通过命令行参数获取路径
    spef_path = args.spef
    output_dir = args.output
    golden_file = args.golden
    # 记录开始时间
    start_time = time.time()
    # 调用计算并保存时延的函数
    output_file = compute_and_save_delays(spef_path, output_dir)
    # 记录结束时间
    end_time = time.time()

    # 计算执行时间
    execution_time = end_time - start_time
    print(f"代码执行时间: {execution_time:.6f} 秒")
   
    evaluate(output_file, golden_file)