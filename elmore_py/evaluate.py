import os
import matplotlib.pyplot as plt

def read_delays_from_file(file_path):
    """从文件中读取时延数据并返回字典格式"""
    delays = {}
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                parts = line.split()
                input_node = parts[0]
                output_node = parts[1]
                delay = float(parts[2])
                delays[(input_node, output_node)] = delay
    return delays

def compare_delays_and_save(calculated_delays, golden_delays, tolerance_relative=0.05, calculated_file=""):
    """比较计算结果与golden data，并输出误差统计，同时绘制散点图"""
    absolute_errors = []
    relative_errors = []
    
    # 用于绘图的数据
    x_values = []  # golden data
    y_values = []  # calculated delay

    for (input_node, output_node), calc_delay in calculated_delays.items():
        if (input_node, output_node) in golden_delays:
            golden_delay = golden_delays[(input_node, output_node)]
            
            # 判断延迟值小于0.05时使用绝对误差，大于等于0.05时使用相对误差
            if golden_delay < tolerance_relative:
                error = abs(calc_delay - golden_delay)
                absolute_errors.append(error)
            else:
                if golden_delay != 0:
                    error = abs((calc_delay - golden_delay) / golden_delay)
                    relative_errors.append(error)
                else:
                    # 如果黄金时延为零，计算绝对误差
                    error = abs(calc_delay - golden_delay)
                    absolute_errors.append(error)
            
            # 添加数据点用于绘图
            x_values.append(golden_delay)
            y_values.append(calc_delay)

    # 输出误差统计信息
    abs_precision = sum(absolute_errors) / len(absolute_errors) if absolute_errors else 0
    rel_precision = sum(relative_errors) / len(relative_errors) if relative_errors else 0

    # 转换相对误差为百分比格式
    rel_precision_percent = rel_precision * 100

    print(f"Average Absolute Error: {abs_precision:.6f}")
    print(f"Average Relative Error: {rel_precision_percent:.2f}%")

    # 获取文件名（不含路径和扩展名）
    base_name = os.path.splitext(os.path.basename(calculated_file))[0]

    # 绘制图形
    plt.figure(figsize=(8, 8))
    plt.scatter(x_values, y_values, color='blue', label='Calculated Delay')  # 绘制散点图
    plt.plot([0, max(x_values)], [0, max(x_values)], color='red', linestyle='--')  # 添加y=x线
    # 添加误差值作为标签
    plt.scatter([], [], color='red', label=f'Avg Abs Error: {abs_precision:.6f}')  # 误差值在图例中的显示
    plt.scatter([], [], color='red', label=f'Avg Rel Error: {rel_precision_percent:.2f}%')  # 误差值在图例中的显示
    
    plt.xlabel('Golden Data (ms)')
    plt.ylabel('Calculated Delay (ms)')
    plt.title(f'Golden Data vs Calculated Delay ({base_name})')

    

    plt.legend(loc='upper left')  # 图例位置调整为左上角
    plt.grid(True)
    plt.show()
    plt.savefig(base_name)  # 保存图片
def evaluate(calculated_file, golden_file):
    """主函数：读取文件，比较时延并输出误差，同时绘制图形"""
    # 读取计算结果文件和黄金数据文件
    calculated_delays = read_delays_from_file(calculated_file)
    golden_delays = read_delays_from_file(golden_file)
    
    # 进行比较并输出误差统计，同时绘制图形
    compare_delays_and_save(calculated_delays, golden_delays, calculated_file=calculated_file)



