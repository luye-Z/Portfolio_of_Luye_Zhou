import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import re

# --- 1. 自动生成递增文件名 (保持你原来的逻辑) ---
def get_next_filename(base_name="tracking_analysis", ext=".png"):
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    save_dir = os.path.join(current_script_dir, 'detection_records_analysis_records')
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    files = os.listdir(save_dir)
    pattern = re.compile(rf"^{base_name}(?:_(\d+))?{ext}$")
    max_num = -1
    found = False
    for f in files:
        match = pattern.match(f)
        if match:
            found = True
            if match.group(1):
                max_num = max(max_num, int(match.group(1)))
            else:
                max_num = max(max_num, 0)
    if not found:
        return os.path.join(save_dir, f"{base_name}{ext}")
    else:
        return os.path.join(save_dir, f"{base_name}_{max_num + 1}{ext}")

# --- 2. 数据准备 ---
SCREEN_WIDTH = 432   # 864 / 2
SCREEN_HEIGHT = 320  # 640 / 2
file_path = "/home/pi/projects/yolo26/video_control/yolo_detect_new_project/detection_records_analyse/detection_records/data_record_20260312_093900.csv"

try:
    # 读取 CSV，并根据你的记录顺序手动指定列名
    # 顺序：timestamp, target_x, target_y, error_x, error_y, pid_out_x, pid_out_y
    column_names = ['timestamp', 'target_x', 'target_y', 'error_x', 'error_y', 'pid_out_x', 'pid_out_y']
    data = pd.read_csv(file_path, names=column_names, header=0)
    
    # --- 3. 核心绘图逻辑修改 (解决 NameError 并优化数据提取) ---
    
    # 过滤掉目标丢失 (坐标为 0) 的无效行，避免曲线“跳水”到 -432
    valid_data = data[(data['target_x'] != 0) & (data['target_y'] != 0)].copy()

    if valid_data.empty:
        print("错误：过滤后没有有效数据，请检查 CSV 文件内容。")
        exit()

    # 直接使用 CSV 里的误差列
    off_x = valid_data['error_x']
    off_y = valid_data['error_y']
    
    # 计算综合欧几里得距离
    distance = np.sqrt(off_x**2 + off_y**2)
    
    # 获取 PID 输出和时间索引
    pid_x = valid_data['pid_out_x']
    pid_y = valid_data['pid_out_y']
    data_index = valid_data['timestamp']

    # --- 4. 绘图美化 ---
    plt.style.use('seaborn-v0_8-muted')
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 14), sharex=True)
    fig.suptitle(f'YOLO Tracking Precision Analysis\nFile: {os.path.basename(file_path)}', fontsize=16, fontweight='bold')

    # 图 1: X/Y 偏移 (误差曲线)
    ax1.plot(data_index, off_x, label='X Error', color='#2E86C1', alpha=0.9)
    ax1.plot(data_index, off_y, label='Y Error', color='#E67E22', alpha=0.9)
    ax1.axhline(0, color='black', linestyle='--', linewidth=1, alpha=0.5)
    ax1.set_ylabel('Pixels Error')
    ax1.set_title('Real-time Tracking Deviation (Error)', fontsize=12, loc='left')
    ax1.legend(loc='upper right')
    ax1.grid(True, linestyle=':', alpha=0.6)

    # 图 2: 综合距离 (总误差)
    ax2.fill_between(data_index, distance, color='#8E44AD', alpha=0.1)
    ax2.plot(data_index, distance, label='Total Distance', color='#8E44AD', linewidth=2)
    ax2.set_ylabel('Distance (px)')
    ax2.set_title('Combined Euclidean Error', fontsize=12, loc='left')
    ax2.legend(loc='upper right')
    ax2.grid(True, linestyle=':', alpha=0.6)

    # 图 3: 控制输出 (PID Response)
    ax3.plot(data_index, pid_x, label='Servo X Output', color='#28B463')
    ax3.plot(data_index, pid_y, label='Servo Y Output', color='#C0392B')
    ax3.set_xlabel('Timestamp')
    ax3.set_ylabel('Control Value')
    ax3.set_title('PID Controller Output', fontsize=12, loc='left')
    ax3.legend(loc='upper right')
    ax3.grid(True, linestyle=':', alpha=0.6)

    # 优化时间戳显示
    plt.xticks(rotation=45)
    # 自动调整 X 轴标签密度
    n = max(1, len(data_index) // 15)
    for i, label in enumerate(ax3.get_xticklabels()):
        if i % n != 0: label.set_visible(False)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    # --- 5. 保存与展示 ---
    save_path = get_next_filename()
    plt.savefig(save_path, dpi=300)
    print(f"分析完成！图表已保存至: {save_path}")
    plt.show()

except Exception as e:
    print(f"程序运行出错: {e}")