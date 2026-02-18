import pandas as pd
import matplotlib.pyplot as plt

# --- 1. 数据准备 ---
SCREEN_WIDTH = 864 / 2
SCREEN_HEIGHT = 640 / 2
file_path = "/home/pi/projects/yolo26/video_control/yolo_detect_new_project/detection_records/record_20260218_093211.csv"

# 尝试读取数据
try:
    data = pd.read_csv(file_path)
except FileNotFoundError:
    print(f"Error: 文件 {file_path} 未找到，请检查路径。")
    # 创建模拟数据用于演示
    import numpy as np
    data = pd.DataFrame({
        'center_x': SCREEN_WIDTH + np.random.normal(0, 50, 100).cumsum(),
        'center_y': SCREEN_HEIGHT + np.random.normal(0, 30, 100).cumsum()
    })

# 计算偏移量和模拟控制输出
data['offset_x'] = data['center_x'] - SCREEN_WIDTH
data['offset_y'] = data['center_y'] - SCREEN_HEIGHT
Kp = 0.1
data['angle_x'] = data['offset_x'] * Kp
data['angle_y'] = data['offset_y'] * Kp

# --- 2. 绘图美化设置 ---
plt.style.use('seaborn-v0_8-muted') # 使用高质感的主题
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
fig.suptitle(f'YOLO Tracking Analysis\nSource: {file_path.split("/")[-1]}', fontsize=16, fontweight='bold')

# --- 3. 绘制偏移量分析图 (Top) ---
ax1.plot(data.index, data['offset_x'], label='X-Axis Offset', color='#2E86C1', linewidth=1.5, alpha=0.8)
ax1.plot(data.index, data['offset_y'], label='Y-Axis Offset', color='#E67E22', linewidth=1.5, alpha=0.8)

# 添加基准线和阴影区（表示死区或稳定区间）
ax1.axhline(0, color='black', linestyle='--', linewidth=1, alpha=0.6)
ax1.fill_between(data.index, -20, 20, color='gray', alpha=0.1, label='Dead Zone (Target)')

ax1.set_title('Real-time Coordinate Deviation', fontsize=13, loc='left')
ax1.set_ylabel('Pixels Offset', fontsize=11)
ax1.grid(True, linestyle=':', alpha=0.6)
ax1.legend(loc='upper right', frameon=True)

# --- 4. 绘制控制响应图 (Bottom) ---
ax2.plot(data.index, data['angle_x'], label='Servo X Output', color='#28B463', linewidth=2)
ax2.plot(data.index, data['angle_y'], label='Servo Y Output', color='#C0392B', linewidth=2)

ax2.set_title('Control System Response (P-Control)', fontsize=13, loc='left')
ax2.set_xlabel('Time (Frames)', fontsize=11)
ax2.set_ylabel('Output Angle', fontsize=11)
ax2.grid(True, linestyle=':', alpha=0.6)
ax2.legend(loc='upper right', frameon=True)

# --- 5. 细节优化与保存 ---
plt.tight_layout(rect=[0, 0.03, 1, 0.95]) # 调整布局给总标题留空

# 如果需要保存图片，取消下面注释
plt.savefig('tracking_analysis.png', dpi=300)

plt.show()