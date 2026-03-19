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

# --- 2. 数据准备与动态列识别 ---
file_path = "/home/pi/projects/yolo26/video_control/yolo_detect_new_project/detection_records_analyse/detection_records/data_record_20260319_095000.csv"

try:
    # 探测列数
    temp_df = pd.read_csv(file_path, nrows=0)
    col_count = len(temp_df.columns)
    
    # 核心映射逻辑
    if col_count == 9:
        # 新版数据：含 Delta 增量
        column_names = ['timestamp', 'target_x', 'target_y', 'error_x', 'error_y', 
                        'delta_x', 'delta_y', 'pid_out_x', 'pid_out_y']
        has_delta = True
        print("检测到新版数据格式 (9列: 含控制增量)")
    else:
        # 老版数据：仅含 绝对输出
        column_names = ['timestamp', 'target_x', 'target_y', 'error_x', 'error_y', 
                        'pid_out_x', 'pid_out_y']
        has_delta = False
        print("检测到老版数据格式 (7列)")

    data = pd.read_csv(file_path, names=column_names, header=0)
    
    # --- 3. 数据清理 ---
    valid_data = data[(data['target_x'] != 0) & (data['target_y'] != 0)].copy()
    if valid_data.empty:
        print("错误：未找到有效追踪数据。")
        exit()

    # --- 4. 绘图美化 ---
    plt.style.use('seaborn-v0_8-muted')
    
    # 如果有 Delta 数据，画 4 张图，否则画 3 张
    num_plots = 4 if has_delta else 3
    fig, axes = plt.subplots(num_plots, 1, figsize=(12, 3.5 * num_plots), sharex=True)
    if num_plots == 1: axes = [axes]

    fig.suptitle(f'YOLO Tracking Precision Analysis\nFile: {os.path.basename(file_path)}', fontsize=15, fontweight='bold')

    curr_ax = 0

    # 图 1: X/Y 误差 (Error)
    axes[curr_ax].plot(valid_data['timestamp'], valid_data['error_x'], label='Error X', color='#2E86C1')
    axes[curr_ax].plot(valid_data['timestamp'], valid_data['error_y'], label='Error Y', color='#E67E22')
    axes[curr_ax].axhline(0, color='black', linestyle='--', alpha=0.3)
    axes[curr_ax].set_ylabel('Pixels')
    axes[curr_ax].set_title('Real-time Tracking Deviation (Error)', fontsize=11, loc='left')
    axes[curr_ax].legend(loc='upper right')
    axes[curr_ax].grid(True, linestyle=':', alpha=0.6)
    curr_ax += 1

    # 图 2: 综合欧几里得距离 (Total Precision)
    dist = np.sqrt(valid_data['error_x']**2 + valid_data['error_y']**2)
    axes[curr_ax].fill_between(valid_data['timestamp'], dist, color='#8E44AD', alpha=0.1)
    axes[curr_ax].plot(valid_data['timestamp'], dist, label='Total Distance', color='#8E44AD', linewidth=1.5)
    axes[curr_ax].set_ylabel('Distance (px)')
    axes[curr_ax].set_title('Combined Precision (Euclidean Distance)', fontsize=11, loc='left')
    axes[curr_ax].grid(True, linestyle=':', alpha=0.6)
    curr_ax += 1

    # 图 3: 控制增量 (Delta) - 仅在新版数据中显示
    if has_delta:
        axes[curr_ax].step(valid_data['timestamp'], valid_data['delta_x'], label='Delta Pan (deg)', color='#1ABC9C', where='post')
        axes[curr_ax].step(valid_data['timestamp'], valid_data['delta_y'], label='Delta Tilt (deg)', color='#D35400', where='post')
        axes[curr_ax].set_ylabel('Degrees Step')
        axes[curr_ax].set_title('Control Intensity (PID Middleware Delta)', fontsize=11, loc='left')
        axes[curr_ax].legend(loc='upper right')
        axes[curr_ax].grid(True, linestyle=':', alpha=0.6)
        curr_ax += 1

    # 图 4: 最终舵机角度 (Servo Output)
    axes[curr_ax].plot(valid_data['timestamp'], valid_data['pid_out_x'], label='Servo Pan', color='#28B463')
    axes[curr_ax].plot(valid_data['timestamp'], valid_data['pid_out_y'], label='Servo Tilt', color='#C0392B')
    axes[curr_ax].set_ylabel('Absolute Degrees')
    axes[curr_ax].set_title('Final Servo Position (PID Output)', fontsize=11, loc='left')
    axes[curr_ax].legend(loc='upper right')
    axes[curr_ax].grid(True, linestyle=':', alpha=0.6)

    # 优化 X 轴时间戳显示
    plt.xticks(rotation=45)
    n = max(1, len(valid_data) // 12)
    for i, label in enumerate(axes[-1].get_xticklabels()):
        if i % n != 0: label.set_visible(False)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    # --- 5. 保存 ---
    save_path = get_next_filename()
    plt.savefig(save_path, dpi=300)
    print(f"处理完成！图表保存至: {save_path}")
    plt.show()

except Exception as e:
    print(f"分析失败: {e}")