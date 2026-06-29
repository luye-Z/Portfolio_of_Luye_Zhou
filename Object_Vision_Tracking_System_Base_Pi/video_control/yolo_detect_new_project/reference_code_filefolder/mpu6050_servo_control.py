import math
import time
from mpu6050 import mpu6050
from rpi_hardware_pwm import HardwarePWM

# --- 硬件配置 ---
MPU_ADDRESS = 0x68
CHIP_ID = 0
TILT_CHANNEL = 1  # GPIO 13
PAN_CHANNEL = 0   # GPIO 12

# --- PID & 滤波参数 ---
ALPHA = 0.98       # 互补滤波系数
K_P = 0.8          # 比例系数 (调整响应强度)
MAX_SERVO_ANGLE = 90

# 初始化硬件
sensor = mpu6050(MPU_ADDRESS)
servo_tilt = HardwarePWM(pwm_channel=TILT_CHANNEL, hz=50, chip=CHIP_ID)
servo_pan = HardwarePWM(pwm_channel=PAN_CHANNEL, hz=50, chip=CHIP_ID)

offsets = {'ax': 0, 'ay': 0, 'az': 0, 'gx': 0, 'gy': 0, 'gz': 0}

def set_angle(pwm_obj, angle):
    """限幅并映射到硬件PWM占空比"""
    angle = max(-MAX_SERVO_ANGLE, min(MAX_SERVO_ANGLE, angle))
    duty = (angle + 90) * (10 / 180) + 2.5
    pwm_obj.change_duty_cycle(duty)

def calibrate():
    global offsets
    print("正在精准校准，请勿触摸传感器...")
    s = {'ax':0,'ay':0,'az':0,'gx':0,'gy':0,'gz':0}
    n = 200
    for _ in range(n):
        a = sensor.get_accel_data()
        g = sensor.get_gyro_data()
        s['ax']+=a['x']; s['ay']+=a['y']; s['az']+=(a['z']-9.80665)
        s['gx']+=g['x']; s['gy']+=g['y']; s['gz']+=g['z']
        time.sleep(0.005)
    offsets = {k: v/n for k, v in s.items()}
    print("校准完成！")

def main():
    calibrate()
    servo_tilt.start(10.0)
    servo_pan.start(7.5)
    
    # 状态变量
    pitch, roll = 0.0, 0.0
    last_time = time.time()
    
    # 目标值 (通常希望云台保持 0 度水平)
    target_pitch, target_roll = 0.0, 0.0

    print("\n[自稳系统已就绪] 正在实时补偿偏移...")

    try:
        while True:
            current_time = time.time()
            dt = current_time - last_time
            if dt < 0.01: # 限制计算频率最高 100Hz
                continue
            last_time = current_time

            # 1. 获取并修正原始数据
            accel = sensor.get_accel_data()
            gyro = sensor.get_gyro_data()
            
            ax = accel['x'] - offsets['ax']
            ay = accel['y'] - offsets['ay']
            az = accel['z'] - offsets['az']
            gx = gyro['x'] - offsets['gx']
            gy = gyro['y'] - offsets['gy']

            # 2. 互补滤波计算当前姿态角度
            # 加速度计静态角
            acc_p = math.degrees(math.atan2(ay, math.sqrt(ax**2 + az**2)))
            acc_r = math.degrees(math.atan2(-ax, az))
            
            # 融合计算
            pitch = ALPHA * (pitch + gy * dt) + (1 - ALPHA) * acc_p
            roll = ALPHA * (roll + gx * dt) + (1 - ALPHA) * acc_r

            # 3. PID 控制输出 (这里仅使用 P 项，如需更稳可加 D 项)
            # 计算偏差：目标角度 - 当前传感器角度
            error_p = target_pitch - pitch
            error_r = target_roll - roll
            
            # 计算舵机控制量 (应用比例增益 K_P)
            # 如果 K_P=1.0，则是全量补偿；K_P < 1.0 可以过滤微小震动
            servo_p_output = error_p * K_P
            servo_r_output = error_r * K_P

            # 4. 执行控制
            set_angle(servo_tilt, servo_r_output+45)
            set_angle(servo_pan, -servo_p_output)

            print(f"Angle: P:{pitch:5.1f} R:{roll:5.1f} | Servo Out: {servo_p_output:5.1f}", end='\r')

    except KeyboardInterrupt:
        print("\n停止控制")
        servo_tilt.stop(); servo_pan.stop()

if __name__ == "__main__":
    main()