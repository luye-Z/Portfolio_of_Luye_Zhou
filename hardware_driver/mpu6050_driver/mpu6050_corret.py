import math
import time
from mpu6050 import mpu6050

# 1. 初始化传感器
sensor = mpu6050(0x68)

# 2. 全局变量
offsets = {'ax': 0, 'ay': 0, 'az': 0, 'gx': 0, 'gy': 0, 'gz': 0}
pitch = 0.0
roll = 0.0
last_time = time.time()

def calibrate_sensor(samples=500):
    """自动校准：计算静止状态下的平均偏差"""
    global offsets
    print(f"开始校准，请保持传感器静止... (采样 {samples} 次)")
    
    sums = {'ax': 0, 'ay': 0, 'az': 0, 'gx': 0, 'gy': 0, 'gz': 0}

    for _ in range(samples):
        accel = sensor.get_accel_data()
        gyro = sensor.get_gyro_data()
        
        sums['ax'] += accel['x']
        sums['ay'] += accel['y']
        sums['az'] += (accel['z'] - 9.80665)  # 减去标准重力
        sums['gx'] += gyro['x']
        sums['gy'] += gyro['y']
        sums['gz'] += gyro['z']
        time.sleep(0.005)

    for key in offsets:
        offsets[key] = sums[key] / samples
    
    print("校准完成！偏置值已应用。")

def get_integrated_angles(curr_pitch, curr_roll, dt):
    """获取应用了互补滤波的角度数据"""
    accel = sensor.get_accel_data()
    gyro = sensor.get_gyro_data()

    # 应用校准值
    ax = accel['x'] - offsets['ax']
    ay = accel['y'] - offsets['ay']
    az = accel['z'] - offsets['az']
    gx = gyro['x'] - offsets['gx']
    gy = gyro['y'] - offsets['gy']

    # 计算加速度计给出的静态角度 (角度制)
    # Pitch: 绕Y轴旋转；Roll: 绕X轴旋转
    accel_pitch = math.atan2(ay, math.sqrt(ax**2 + az**2)) * 180 / math.pi
    accel_roll = math.atan2(-ax, az) * 180 / math.pi

    # 互补滤波算法
    # 陀螺仪积分项: curr_angle + gyro_rate * dt
    # alpha 取 0.98，代表 98% 信任陀螺仪，2% 信任加速度计纠偏
    alpha = 0.98
    new_pitch = alpha * (curr_pitch + gy * dt) + (1 - alpha) * accel_pitch
    new_roll = alpha * (curr_roll + gx * dt) + (1 - alpha) * accel_roll

    return new_pitch, new_roll

# --- 主程序执行 ---

# 第一步：校准
calibrate_sensor(500)

print("\n开始实时读取角度数据 (Ctrl+C 停止)...")
print("-" * 45)

try:
    while True:
        # 计算时间增量 dt
        current_time = time.time()
        dt = current_time - last_time
        last_time = current_time

        # 获取融合后的角度
        pitch, roll = get_integrated_angles(pitch, roll, dt)

        # 打印结果
        print(f"俯仰角(Pitch): {pitch:7.2f}° | 翻滚角(Roll): {roll:7.2f}°", end='\r')
        
        # 建议频率在 20Hz - 100Hz 之间 (0.05s - 0.01s)
        time.sleep(0.02)

except KeyboardInterrupt:
    print("\n\n程序已安全停止。")