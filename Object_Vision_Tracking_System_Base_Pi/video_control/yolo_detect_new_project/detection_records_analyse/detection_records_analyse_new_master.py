import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import re

# --- 配置路径 ---
INPUT_DIR = "/home/pi/projects/yolo26/video_control/yolo_detect_new_project/detection_records_analyse/detection_records"
OUTPUT_DIR = "/home/pi/projects/yolo26/video_control/yolo_detect_new_project/detection_records_analyse/detection_records_analysis_records"

# 确保输出目录存在
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def get_output_path(input_file_name):
    """根据输入文件名生成对应的输出图片路径"""
    name_without_ext = os.path.splitext(input_file_name)[0]
    output_name = name_without_ext.replace("data_record_", "data_analyse_chart_", 1) + ".png"
    return os.path.join(OUTPUT_DIR, output_name)

def process_file(file_path, save_path):
    """核心绘图逻辑（封装你原来的绘图代码）"""
    try:
        # 探测列数
        temp_df = pd.read_csv(file_path, nrows=0)
        col_count = len(temp_df.columns)
        
        if col_count == 9:
            column_names = ['timestamp', 'target_x', 'target_y', 'error_x', 'error_y', 
                            'delta_x', 'delta_y', 'pid_out_x', 'pid_out_y']
            has_delta = True
        else:
            column_names = ['timestamp', 'target_x', 'target_y', 'error_x', 'error_y', 
                            'pid_out_x', 'pid_out_y']
            has_delta = False

        data = pd.read_csv(file_path, names=column_names, header=0)
        valid_data = data[(data['target_x'] != 0) & (data['target_y'] != 0)].copy()
        
        if valid_data.empty:
            print(f"跳过: {os.path.basename(file_path)} (无有效追踪数据)")
            return

        plt.style.use('seaborn-v0_8-muted')
        num_plots = 4 if has_delta else 3
        fig, axes = plt.subplots(num_plots, 1, figsize=(12, 3.5 * num_plots), sharex=True)
        if num_plots == 1: axes = [axes]

        fig.suptitle(f'YOLO Tracking Analysis - {os.path.basename(file_path)}', fontsize=14, fontweight='bold')

        curr_ax = 0
        # 图 1: Error
        axes[curr_ax].plot(valid_data['timestamp'], valid_data['error_x'], label='Error X', color='#2E86C1')
        axes[curr_ax].plot(valid_data['timestamp'], valid_data['error_y'], label='Error Y', color='#E67E22')
        axes[curr_ax].set_ylabel('Pixels')
        axes[curr_ax].set_title('Tracking Error', loc='left')
        axes[curr_ax].legend(loc='upper right'); axes[curr_ax].grid(True, linestyle=':')
        curr_ax += 1

        # 图 2: Euclidean Distance
        dist = np.sqrt(valid_data['error_x']**2 + valid_data['error_y']**2)
        axes[curr_ax].fill_between(valid_data['timestamp'], dist, color='#8E44AD', alpha=0.1)
        axes[curr_ax].plot(valid_data['timestamp'], dist, label='Total Distance', color='#8E44AD')
        axes[curr_ax].set_ylabel('Distance (px)')
        axes[curr_ax].grid(True, linestyle=':')
        curr_ax += 1

        # 图 3: Delta (如果是新数据)
        if has_delta:
            axes[curr_ax].step(valid_data['timestamp'], valid_data['delta_x'], label='Delta Pan', color='#1ABC9C', where='post')
            axes[curr_ax].step(valid_data['timestamp'], valid_data['delta_y'], label='Delta Tilt', color='#D35400', where='post')
            axes[curr_ax].set_ylabel('Delta Deg')
            axes[curr_ax].legend(loc='upper right'); axes[curr_ax].grid(True, linestyle=':')
            curr_ax += 1

        # 图 4/3: Final Output
        axes[curr_ax].plot(valid_data['timestamp'], valid_data['pid_out_x'], label='Pan Out', color='#28B463')
        axes[curr_ax].plot(valid_data['timestamp'], valid_data['pid_out_y'], label='Tilt Out', color='#C0392B')
        axes[curr_ax].set_ylabel('Degrees')
        axes[curr_ax].legend(loc='upper right'); axes[curr_ax].grid(True, linestyle=':')

        # X轴优化
        plt.xticks(rotation=45)
        n = max(1, len(valid_data) // 10)
        for i, lbl in enumerate(axes[-1].get_xticklabels()):
            if i % n != 0: lbl.set_visible(False)

        plt.tight_layout(rect=[0, 0.03, 1, 0.96])
        plt.savefig(save_path, dpi=150) # 批量处理时dpi可以适当降低提高速度
        plt.close(fig) # 重要：关闭窗口释放内存，防止树莓派内存溢出
        print(f"成功生成: {os.path.basename(save_path)}")

    except Exception as e:
        print(f"处理文件 {os.path.basename(file_path)} 失败: {e}")

def main():
    print("开始扫描新数据...")
    # 获取输入文件夹内所有 CSV 文件
    csv_files = [f for f in os.listdir(INPUT_DIR) if f.endswith('.csv')]
    
    new_files_count = 0
    for csv_file in csv_files:
        input_path = os.path.join(INPUT_DIR, csv_file)
        output_path = get_output_path(csv_file)
        
        # 比对：如果输出文件不存在，则是新数据
        if not os.path.exists(output_path):
            print(f"检测到新数据: {csv_file}")
            process_file(input_path, output_path)
            new_files_count += 1
            
    if new_files_count == 0:
        print("未发现新数据，一切都是最新的。")
    else:
        print(f"任务完成！本次共处理 {new_files_count} 个新文件。")

if __name__ == "__main__":
    main()