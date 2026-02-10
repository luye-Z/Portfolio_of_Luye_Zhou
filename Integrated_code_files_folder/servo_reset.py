from gpiozero import AngularServo
from time import sleep

# --- 树莓派 5 硬件适配说明 ---
# 树莓派 5 的硬件 PWM 性能极佳，但需要确保你的系统是最新的
# 建议通过 sudo apt update && sudo apt upgrade 更新系统

# --- 硬件引脚配置 ---
# 注意：在树莓派 5 上，GPIO 12 和 13 是非常理想的 PWM 引脚
SERVOR_MOTOR_PAN = 13
SERVOR_MOTOR_TILT = 12
SERVO_PINS = [SERVOR_MOTOR_PAN, SERVOR_MOTOR_TILT]

# 针对小型舵机（如 SG90/MG90S）在树莓派 5 上的参数优化
SERVO_CONFIG = {
    "min_angle": 0,
    "max_angle": 180,
    "min_pulse_width": 0.0006,  # 提高 0.1ms 避开机械死区，彻底解决 0 度抽风
    "max_pulse_width": 0.0024   # 降低 0.1ms 防止末端震荡
}

print(f"--- Raspberry Pi 5 Servo System ---")
servos = []

# 初始化
for pin in SERVO_PINS:
    try:
        # gpiozero 会在树莓派 5 上自动尝试最适合的驱动（通常是 lgpio）
        servo = AngularServo(pin, **SERVO_CONFIG)
        servos.append(servo)
        
        servo_pan = servos[0]
        servo_tilt = servos[1]
        
        print(f"[OK] GPIO {pin} Ready")
    except Exception as e:
        print(f"[Error] Pin {pin} initialization failed: {e}")

# def test_sequence():
#     # --- 阶段 1: 0度 ---
#     print("\nMoving to 0°...")
#     for s in servos:
#         s.angle = 0
#     sleep(0.8)  # 树莓派5响应极快，1.0s足够了
    
#     for s in servos:
#         s.value = None  # 释放信号：树莓派5不再发送脉冲，舵机进入静默模式
#     print("Signal Detached: Jitter should be zero.")
#     sleep(0.5)

#     # --- 阶段 2: 45度 ---
#     print("Moving to 45°...")
#     for s in servos:
#         s.angle = 45
#     sleep(0.8)
    
#     for s in servos:
#         s.value = None
#     print("Signal Detached: Jitter should be zero.")
#     sleep(0.5)
def test_sequence():
    

    servo_tilt.angle = 0
    servo_pan.angle = 0
    sleep(0.5)
    servo_tilt.angle = 10
    servo_pan.angle = 10
    sleep(0.5)
    servo_tilt.angle = 20
    servo_pan.angle = 20
    sleep(0.5)
    servo_tilt.angle = 30
    servo_pan.angle = 30
    sleep(0.5)
    servo_tilt.angle = 40
    servo_pan.angle = 40
    sleep(0.5)

try:
    print("Starting Loop (RPi 5 Optimized)")
    while True:
        test_sequence()
except KeyboardInterrupt:
    print("\nStopping...")
finally:
    for s in servos:
        s.angle = None
    print("Safe to quit.")
