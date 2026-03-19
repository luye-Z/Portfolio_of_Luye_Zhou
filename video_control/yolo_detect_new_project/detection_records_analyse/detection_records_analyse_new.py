import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import re

# --- 1. 自动生成递增文件名 ---
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
    return os.path.join(save_dir, f"{base_name}_{max_num + 1}{ext}" if found else f"{base_name}{ext}")

# --- 2. 数据准备与兼容性读取 ---
file_path = "/home/pi/projects/yolo26/video_control/yolo_detect_new_project/detection_records_analyse/detection_records/data_record_20260312_093900.csv"

try:
    # 先读取第一行探测列数
    temp_df = pd.read_csv(file_path, nrows=0)
    col_count = len(temp_df.columns)
    
    # 根据列数定义列名
    if col_count == 9:
        # 新版数据格式
        column_names = ['timestamp', 'target_x', 'target_y', 'kalman_x', 'kalman_y', 'error_x', 'error_y', 'pid_out_x', 'pid_out_y']
        has_kalman = True
    else:
        # 旧版数据格式 (7列)
        column_names = ['timestamp', 'target_x', 'target_y', 'error_x', 'error_y', 'pid_out_x', 'pid_out_y']
        has_kalman = False

    data = pd.read_csv(file_path, names=column_names, header=0)
    
    # --- 3. 数据过滤 ---
    valid_data = data[(data['target_x'] != 0) & (data['target_y'] != 0)].copy()
    if valid_data.empty:
        print("错误：过滤后没有有效数据。")
        exit()

    # --- 4. 绘图美化 ---
    plt.style.use('seaborn-v0_8-muted')
    # 如果有卡尔曼数据，我们增加一个子图用来对比滤波效果，共 4 个子图
    num_subplots = 4 if has_kalman else 3
    fig, axes = plt.subplots(num_subplots, 1, figsize=(12, 4 * num_subplots), sharex=True)
    
    # 兼容处理 axes (如果只有1个子图 axes 不是列表)
    if num_subplots == 1: axes = [axes]
    
    fig.suptitle(f'YOLO Tracking Analysis (Kalman: {"Enabled" if has_kalman else "None"})\nFile: {os.path.basename(file_path)}', 
                 fontsize=16, fontweight='bold')

    idx = 0
    # 图 1: Kalman 对比 (仅在新数据中显示)
    if has_kalman:
        ax_k = axes[idx]
        ax_k.plot(valid_data['timestamp'], valid_data['target_x'], label='Raw Target X', color='gray', alpha=0.4, linestyle='--')
        ax_k.plot(valid_data['timestamp'], valid_data['kalman_x'], label='Kalman Filter X', color='#2E86C1', linewidth=2)
        ax_k.set_ylabel('Coordinate X')
        ax_k.set_title('Kalman Filtering Effect (X-axis)', fontsize=12, loc='left')
        ax_k.legend(loc='upper right')
        ax_k.grid(True, linestyle=':', alpha=0.6)
        idx += 1

    # 图 2: 误差曲线
    ax_err = axes[idx]
    ax_err.plot(valid_data['timestamp'], valid_data['error_x'], label='X Error', color='#2E86C1')
    ax_err.plot(valid_data['timestamp'], valid_data['error_y'], label='Y Error', color='#E67E22')
    ax_err.axhline(0, color='black', linestyle='--', linewidth=1, alpha=0.5)
    ax_err.set_ylabel('Pixels Error')
    ax_err.set_title('Real-time Tracking Deviation', fontsize=12, loc='left')
    ax_err.legend(loc='upper right')
    ax_err.grid(True, linestyle=':', alpha=0.6)
    idx += 1

    # 图 3: 综合距离
    ax_dist = axes[idx]
    distance = np.sqrt(valid_data['error_x']**2 + valid_data['error_y']**2)
    ax_dist.fill_between(valid_data['timestamp'], distance, color='#8E44AD', alpha=0.1)
    ax_dist.plot(valid_data['timestamp'], distance, label='Total Distance', color='#8E44AD', linewidth=2)
    ax_dist.set_ylabel('Distance (px)')
    ax_dist.set_title('Combined Euclidean Error', fontsize=12, loc='left')
    ax_dist.legend(loc='upper right')
    ax_dist.grid(True, linestyle=':', alpha=0.6)
    idx += 1

    # 图 4: PID 输出
    ax_pid = axes[idx]
    ax_pid.plot(valid_data['timestamp'], valid_data['pid_out_x'], label='Servo X Output', color='#28B463')
    ax_pid.plot(valid_data['timestamp'], valid_data['pid_out_y'], label='Servo Y Output', color='#C0392B')
    ax_pid.set_xlabel('Timestamp')
    ax_pid.set_ylabel('Control Value')
    ax_pid.set_title('PID Controller Output', fontsize=12, loc='left')
    ax_pid.legend(loc='upper right')
    ax_pid.grid(True, linestyle=':', alpha=0.6)

    # 优化时间戳显示
    plt.xticks(rotation=45)
    n = max(1, len(valid_data) // 15)
    for i, label in enumerate(ax_pid.get_xticklabels()):
        if i % n != 0: label.set_visible(False)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    # --- 5. 保存与展示 ---
    save_path = get_next_filename(base_name="tracking_analysis_kalman" if has_kalman else "tracking_analysis")
    plt.savefig(save_path, dpi=300)
    print(f"分析完成！格式: {'新版' if has_kalman else '旧版'}, 保存至: {save_path}")
    plt.show()

except Exception as e:
    print(f"程序运行出错: {e}")