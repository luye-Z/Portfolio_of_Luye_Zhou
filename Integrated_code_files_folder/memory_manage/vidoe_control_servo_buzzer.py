import cv2
from picamera2 import Picamera2
from ultralytics import YOLO
from rpi_hardware_pwm import HardwarePWM
import RPi.GPIO as GPIO
import threading
import time

# —————————————————————————————— 0. 配置区域 ——————————————————————————————
# 画面分辨率
SCREEN_WIDTH = 864
SCREEN_HEIGHT = 640

# 舵机追踪配置
DEG_PER_PIX = 77.0 / SCREEN_WIDTH  # 像素转角度比例
Kp_PAN = 0.2                       # 水平平滑系数
Kp_TILT = 0.15                     # 垂直平滑系数
DEAD_ZONE_X = 40                   # 水平死区（像素）
DEAD_ZONE_Y = 40                   # 垂直死区（像素）

# 舵机物理限位
SERVO_MIN, SERVO_MAX = -89, 89

# 蜂鸣器逻辑配置
BUZZER_PIN = 25
DELAY_THRESHOLD = 0.8              # 持续检测 0.8s 触发报警

# —————————————————————————————— 1. 硬件初始化 ——————————————————————————————
# GPIO 初始化 (蜂鸣器)
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUZZER_PIN, GPIO.OUT)
buzzer_active = threading.Event()

# Hardware PWM 初始化 (舵机)
# Chip 0, Channel 0 为 Tilt, Channel 1 为 Pan
servo_tilt = HardwarePWM(pwm_channel=0, hz=50, chip=0)
servo_pan = HardwarePWM(pwm_channel=1, hz=50, chip=0)
servo_tilt.start(7.5) # 归中
servo_pan.start(7.5)  # 归中

# 运行角度记录
servo_pan_angle = 0.0
servo_tilt_angle = 0.0

# 相机初始化
picam2 = Picamera2()
config = picam2.create_preview_configuration(main={
    "size": (SCREEN_WIDTH, SCREEN_HEIGHT), 
    "format": "RGB888"
})
picam2.configure(config)
picam2.start()

# 模型加载
model = YOLO("/home/pi/projects/yolo26/model_folder/ncnn_format_model/640_imgsz_ncnn_model/0207_quadcopter_yolo26_ncnn_model", task='detect')

# —————————————————————————————— 2. 功能函数 ——————————————————————————————

def set_servo_angle(pwm_obj, angle):
    """将 -90~90 度映射到 2.5~12.5% 占空比"""
    angle = max(SERVO_MIN, min(SERVO_MAX, angle))
    duty = (angle + 90) * (10 / 180) + 2.5
    pwm_obj.change_duty_cycle(duty)

def blink_handler():
    """后台蜂鸣器工作线程"""
    while True:
        buzzer_active.wait() # 等待信号唤醒
        GPIO.output(BUZZER_PIN, GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(BUZZER_PIN, GPIO.LOW)
        time.sleep(0.1)
        # 如果 buzzer_active 被 clear()，下次循环将在此 wait() 处阻塞

# 启动蜂鸣器守护线程
threading.Thread(target=blink_handler, daemon=True).start()

# —————————————————————————————— 3. 主循环 ——————————————————————————————
first_detected_time = None

print("系统就绪: YOLO + 舵机追踪 + 延迟蜂鸣器")
try:
    while True:
        frame = picam2.capture_array()
        # 启用 stream 模式
        results = model(frame, imgsz=640, conf=0.3, verbose=False, stream=True)

        annotated_frame = frame.copy()
        current_frame_valid = False
        target_x, target_y = None, None

        # 解析检测
        for result in results:  # 遍历生成器返回的每一帧检测结果
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                w, h = x2 - x1, y2 - y1

                # 过滤异常大框
                if w >= (SCREEN_WIDTH * 0.7) or h >= (SCREEN_HEIGHT * 0.7):
                    continue

                current_frame_valid = True
                target_x = (x1 + x2) / 2
                target_y = (y1 + y2) / 2

                # 绘制UI
                cv2.rectangle(annotated_frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                cv2.circle(annotated_frame, (int(target_x), int(target_y)), 5, (0, 0, 255), -1)
                break # 单目标追踪：取第一符合条件的

        # --- A. 舵机追踪逻辑 ---
        if current_frame_valid:
            # 计算相对于画面中心的偏移
            error_x = target_x - (SCREEN_WIDTH / 2)
            error_y = target_y - (SCREEN_HEIGHT / 2)

            # PAN 轴控制
            if abs(error_x) > DEAD_ZONE_X:
                servo_pan_angle -= (error_x * DEG_PER_PIX) * Kp_PAN
                set_servo_angle(servo_pan, servo_pan_angle)

            # TILT 轴控制
            if abs(error_y) > DEAD_ZONE_Y:
                servo_tilt_angle += (error_y * DEG_PER_PIX) * Kp_TILT
                set_servo_angle(servo_tilt, servo_tilt_angle)

        # --- B. 蜂鸣器延迟告警逻辑 ---
        if current_frame_valid:
            if first_detected_time is None:
                first_detected_time = time.time()
            
            duration = time.time() - first_detected_time
            if duration >= DELAY_THRESHOLD:
                if not buzzer_active.is_set():
                    buzzer_active.set()
        else:
            first_detected_time = None
            if buzzer_active.is_set():
                buzzer_active.clear()

        # --- C. 画面渲染 ---
        # 缩小预览画面以降低显示开销
        display_frame = cv2.resize(annotated_frame, (820, 616))
        # 绘制中心死区参考框
        cv_dz_x = int(DEAD_ZONE_X * (820/SCREEN_WIDTH))
        cv_dz_y = int(DEAD_ZONE_Y * (616/SCREEN_HEIGHT))
        cv2.rectangle(display_frame, 
                      (410 - cv_dz_x, 308 - cv_dz_y), 
                      (410 + cv_dz_x, 308 + cv_dz_y), (255, 255, 0), 1)
        
        cv2.imshow("Pi5 Tracking System", display_frame)

        if cv2.waitKey(1) == ord("q"):
            break

finally:
    print("\n正在释放资源...")
    buzzer_active.clear()
    picam2.stop()
    servo_pan.stop()
    servo_tilt.stop()
    cv2.destroyAllWindows()
    GPIO.cleanup()
