import cv2
import math
import time
import threading
import RPi.GPIO as GPIO
from picamera2 import Picamera2
from ultralytics import YOLO
from rpi_hardware_pwm import HardwarePWM

# —————————————————————————————— 0. 配置区域 ——————————————————————————————
# 画面分辨率
SCREEN_WIDTH = 864
SCREEN_HEIGHT = 640
SCREEN_DIAG = (SCREEN_WIDTH**2 + SCREEN_HEIGHT**2)**0.5  #屏幕对角线像素

# --- 精准视场角 (FOV) 计算 ---
DFOV = 77.0  # 对角线视场角
# HFOV = DFOV*
# VFOV 
# 计算水平视场角 (HFOV) 并得到每像素角度
hfov_rad = 2 * math.atan(math.tan(math.radians(DFOV) / 2) * (SCREEN_WIDTH / SCREEN_DIAG))
DEG_PER_PIX = math.degrees(hfov_rad) / SCREEN_WIDTH  # 约为 0.0742

# --- PD 控制器参数 ---
# Kp: 比例系数 (响应速度), Kd: 微分系数 (阻尼/防震荡)
Kp_PAN, Kd_PAN = 0.38, 0.06
Kp_TILT, Kd_TILT = 0.38, 0.06

DEAD_ZONE_X = 6  # 水平死区（像素）
DEAD_ZONE_Y = 6  # 垂直死区（像素）

# 舵机物理限位
SERVO_MIN, SERVO_MAX = -90, 90

# 蜂鸣器逻辑配置
BUZZER_PIN = 25
DELAY_THRESHOLD = 0.8  # 持续检测 0.8s 触发报警

# —————————————————————————————— 1. 硬件初始化 ——————————————————————————————
# GPIO 初始化 (蜂鸣器)
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUZZER_PIN, GPIO.OUT)
buzzer_active = threading.Event()

# Hardware PWM 初始化 (舵机)
# 假设: Chip 0, Channel 1 为 Pan (GPIO 13), Channel 0 为 Tilt (GPIO 12)
# 请根据实际接线调整 pwm_channel
servo_pan = HardwarePWM(pwm_channel=0, hz=50, chip=0)   
servo_tilt = HardwarePWM(pwm_channel=1, hz=50, chip=0)  

# 初始角度设置
servo_pan_angle = 0.0
servo_tilt_angle = 90.0  # 根据你之前的设定，初始上仰 90 度

def set_servo_angle(pwm_obj, angle):
    """将 -90~90 度映射到 2.5~12.5% 占空比"""
    angle = max(SERVO_MIN, min(SERVO_MAX, angle))
    duty = (angle + 90) * (10 / 180) + 2.5
    pwm_obj.change_duty_cycle(duty)

# 执行初始化位置
set_servo_angle(servo_pan, servo_pan_angle)
set_servo_angle(servo_tilt, servo_tilt_angle)
servo_pan.start(7.5)
servo_tilt.start(12.5)

# 相机初始化
picam2 = Picamera2()
config = picam2.create_preview_configuration(main={
    "size": (SCREEN_WIDTH, SCREEN_HEIGHT), 
    "format": "RGB888"
})
picam2.configure(config)
picam2.start()

# 模型加载 (请确保路径正确)
model = YOLO("/home/pi/projects/yolo26/model_folder/ncnn_format_model/640_imgsz_ncnn_model/0207_quadcopter_yolo26_ncnn_model", task='detect')

# —————————————————————————————— 2. 功能函数 ——————————————————————————————

def blink_handler():
    """后台蜂鸣器工作线程"""
    while True:
        buzzer_active.wait() 
        GPIO.output(BUZZER_PIN, GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(BUZZER_PIN, GPIO.LOW)
        time.sleep(0.1)

threading.Thread(target=blink_handler, daemon=True).start()

# —————————————————————————————— 3. 主循环 ——————————————————————————————
# PD 状态变量
last_error_x = 0
last_error_y = 0
last_time = time.time()
first_detected_time = None

# 性能统计
frame_count = 0
total_inference_time = 0.0

print(f"系统就绪: PD控制模式 | HFOV: {math.degrees(hfov_rad):.2f}°")

try:
    while True:
        start_time = time.time()
        frame = picam2.capture_array()
        
        # 推理
        results = model(frame, imgsz=640, conf=0.3, verbose=False, stream=True)

        annotated_frame = frame.copy()
        current_frame_valid = False
        target_x, target_y = None, None
        confidence = 0.0

        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                w, h = x2 - x1, y2 - y1
                confidence = box.conf[0].item()

                # 过滤异常大框
                if w >= (SCREEN_WIDTH * 0.8) or h >= (SCREEN_HEIGHT * 0.8):
                    continue

                current_frame_valid = True
                target_x = (x1 + x2) / 2
                target_y = (y1 + y2) / 2
                
                cv2.rectangle(annotated_frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                cv2.circle(annotated_frame, (int(target_x), int(target_y)), 5, (0, 0, 255), -1)
                break

        # --- A. PD 舵机追踪逻辑 ---
        current_time = time.time()
        dt = current_time - last_time
        if dt == 0: dt = 0.001 # 防止除零

        if current_frame_valid:
            # 计算当前误差 (距离中心点)
            error_x = target_x - (SCREEN_WIDTH / 2)
            error_y = target_y - (SCREEN_HEIGHT / 2)

            # 微分项: 误差的变化率 (速度)
            derivative_x = (error_x - last_error_x) / dt
            derivative_y = (error_y - last_error_y) / dt

            # Pan 水平轴控制 (注意符号：左偏需要减角度还是加角度需根据舵机方向实测)
            if abs(error_x) > DEAD_ZONE_X:
                # 核心 PD 公式: Output = Kp*e + Kd*de/dt
                adj_x = (error_x * Kp_PAN + derivative_x * Kd_PAN) * DEG_PER_PIX
                servo_pan_angle -= adj_x
                servo_pan_angle = max(SERVO_MIN, min(SERVO_MAX, servo_pan_angle))
                set_servo_angle(servo_pan, servo_pan_angle)

            # Tilt 垂直轴控制
            if abs(error_y) > DEAD_ZONE_Y:
                adj_y = (error_y * Kp_TILT + derivative_y * Kd_TILT) * DEG_PER_PIX
                servo_tilt_angle += adj_y
                servo_tilt_angle = max(SERVO_MIN, min(SERVO_MAX, servo_tilt_angle))
                set_servo_angle(servo_tilt, servo_tilt_angle)

            # 更新 PD 状态
            last_error_x = error_x
            last_error_y = error_y
        else:
            # 丢失目标，重置微分项防止下次突跳
            last_error_x, last_error_y = 0, 0
        
        last_time = current_time

        # --- B. 蜂鸣器逻辑 ---
        if current_frame_valid:
            if first_detected_time is None: first_detected_time = time.time()
            if (time.time() - first_detected_time) >= DELAY_THRESHOLD:
                if not buzzer_active.is_set(): buzzer_active.set()
        else:
            first_detected_time = None
            if buzzer_active.is_set(): buzzer_active.clear()

        # --- C. UI 与 显示 ---
        # 绘制中心死区参考框
        cv2.rectangle(annotated_frame, 
                      (int(SCREEN_WIDTH/2 - DEAD_ZONE_X), int(SCREEN_HEIGHT/2 - DEAD_ZONE_Y)), 
                      (int(SCREEN_WIDTH/2 + DEAD_ZONE_X), int(SCREEN_HEIGHT/2 + DEAD_ZONE_Y)), 
                      (255, 255, 0), 1)

        if current_frame_valid:
            cv2.putText(annotated_frame, f"Conf: {confidence:.2f} Pan:{servo_pan_angle:.1f} Tilt:{servo_tilt_angle:.1f}", 
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        cv2.imshow("PD Tracking System", annotated_frame)

        frame_count += 1
        total_inference_time += (time.time() - start_time)
        if cv2.waitKey(1) == ord("q"):
            break

finally:
    print("\n正在安全关闭...")
    buzzer_active.clear()
    picam2.stop()
    # 舵机复位
    set_servo_angle(servo_tilt, 90)
    set_servo_angle(servo_pan, 0)
    time.sleep(1.0)
    servo_pan.stop()
    servo_tilt.stop()
    cv2.destroyAllWindows()
    GPIO.cleanup()
    
    if frame_count > 0:
        print(f"平均帧率: {frame_count / total_inference_time:.2f} FPS")