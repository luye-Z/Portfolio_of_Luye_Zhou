import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import re

# --- 1. 自动生成递增文件名 ---
def get_next_filename(base_name="tracking_analysis", ext=".png"):
    # 设置保存文件的路径
    save_dir = './detection_records_analysis_records'
    
    # 确保目录存在
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    # 获取目标目录下所有文件
    files = os.listdir(save_dir)
    
    # 匹配 base_name + _n + ext 的模式
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

# --- 2. 数据准备与计算 ---
SCREEN_WIDTH = 864 / 2
SCREEN_HEIGHT = 640 / 2
file_path = "/home/pi/projects/yolo26/video_control/yolo_detect_new_project/detection_records/record_20260304_151409.csv"

try:
    data = pd.read_csv(file_path)
except FileNotFoundError:
    print(f"File {file_path} not found, using dummy data.")
    data = pd.DataFrame({
        'center_x': SCREEN_WIDTH + np.random.normal(0, 50, 100).cumsum(),
        'center_y': SCREEN_HEIGHT + np.random.normal(0, 30, 100).cumsum()
    })

# 计算偏移量
data['offset_x'] = data['center_x'] - SCREEN_WIDTH
data['offset_y'] = data['center_y'] - SCREEN_HEIGHT

# 改动 2：计算欧几里得距离 (Target Distance)
# $distance = \sqrt{offset_x^2 + offset_y^2}$
data['distance'] = np.sqrt(data['offset_x']**2 + data['offset_y']**2)

# 计算控制输出
Kp = 0.1
data['angle_x'] = data['offset_x'] * Kp
data['angle_y'] = data['offset_y'] * Kp

# --- 3. 绘图美化设置 (三行子图) ---
plt.style.use('seaborn-v0_8-muted')
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 14), sharex=True)
fig.suptitle(f'YOLO Tracking & Stability Analysis\nSource: {file_path.split("/")[-1]}', fontsize=16, fontweight='bold')

# 图 1: X/Y 偏移
ax1.plot(data.index, data['offset_x'], label='X Offset', color='#2E86C1', alpha=0.8)
ax1.plot(data.index, data['offset_y'], label='Y Offset', color='#E67E22', alpha=0.8)
ax1.axhline(0, color='black', linestyle='--', linewidth=1, alpha=0.5)
ax1.set_ylabel('Pixels Offset')
ax1.set_title('Coordinate Deviation', fontsize=12, loc='left')
ax1.legend(loc='upper right')
ax1.grid(True, linestyle=':', alpha=0.6)

# 图 2: 综合距离 (改动点)
ax2.fill_between(data.index, data['distance'], color='#8E44AD', alpha=0.2)
ax2.plot(data.index, data['distance'], label='Total Distance (Error)', color='#8E44AD', linewidth=2)
ax2.set_ylabel('Distance (px)')
ax2.set_title('Combined Tracking Error (Euclidean Distance)', fontsize=12, loc='left')
ax2.legend(loc='upper right')
ax2.grid(True, linestyle=':', alpha=0.6)

# 图 3: 控制输出
ax3.plot(data.index, data['angle_x'], label='Servo X', color='#28B463')
ax3.plot(data.index, data['angle_y'], label='Servo Y', color='#C0392B')
ax3.set_xlabel('Time (Frames)')
ax3.set_ylabel('Angle Output')
ax3.set_title('Servo Control Response', fontsize=12, loc='left')
ax3.legend(loc='upper right')
ax3.grid(True, linestyle=':', alpha=0.6)

# --- 4. 保存与展示 ---
plt.tight_layout(rect=[0, 0.03, 1, 0.95])

save_name = get_next_filename()
plt.savefig(save_name, dpi=300)
print(f"分析图表已保存为: {save_name}")

plt.show()