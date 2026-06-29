import cv2
from picamera2 import Picamera2
from ultralytics import YOLO
import RPi.GPIO as GPIO
import threading
import time

# --- 0. 配置与初始化 ---

# 画面分辨率
FRAME_WIDTH = 1640
FRAME_HEIGHT = 1232

# GPIO 引脚配置
BUZZER_PIN = 25
GPIO.setmode(GPIO.BCM) #BCM模式指的是使用Broadcom芯片的原始GPIO编号方式,而不是物理引脚的编号
GPIO.setup(BUZZER_PIN, GPIO.OUT)

# 计时器与阈值配置
first_detected_time = None  # 记录目标首次出现的时刻
DELAY_THRESHOLD = 0.8       # 设定持续检测阈值（秒）

# 线程同步事件：控制蜂鸣器是否“鸣叫”
buzzer_active = threading.Event() 

# --- 1. 后台蜂鸣器线程函数 ---
def blink_handler():
    while True:
        # 1. 阻塞等待：如果事件没被 set，线程会在这里“死掉”一样停住，完全不占 CPU
        # 如果事件被 set 了，它会立刻冲过去执行下面的代码
        buzzer_active.wait() 
        
        # 2. 一旦醒来，说明需要响了
        GPIO.output(BUZZER_PIN, GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(BUZZER_PIN, GPIO.LOW)
        time.sleep(0.1)

# 启动后台线程并设置为守护线程
blink_thread = threading.Thread(target=blink_handler, daemon=True)
blink_thread.start()
print(f"蜂鸣器后台线程已启动,引脚 {BUZZER_PIN} 已配置为输出模式")

# --- 2. 相机与模型配置 ---
picam2 = Picamera2()
config = picam2.create_preview_configuration(main={
    "size": (FRAME_WIDTH, FRAME_HEIGHT), 
    "format": "RGB888"
})
picam2.configure(config)
picam2.start()

# 加载 NCNN 模型 (树莓派 5 推荐使用 NCNN 以获得最高 FPS)
model = YOLO("yolo26n_01_24_quadcopter_best_ncnn_model", task='detect')

print("程序已启动...")
print(f"设定：持续检测到目标 {DELAY_THRESHOLD} 秒后将激活蜂鸣器。")
print("按下 'q' 键退出程序。")

# --- 3. 主循环 ---
try:
    while True:
        # 获取图像帧
        frame = picam2.capture_array()
        
        # YOLO 推理
        # imgsz=320 提升推理速度,conf=0.25 过滤低置信度
        results = model(frame, imgsz=320, conf=0.25, verbose=False)
        
        annotated_frame = frame.copy() 
        current_frame_target_valid = False  # 标记本帧是否检测到“有效”目标

        # 解析检测结果
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # 获取坐标
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                width = x2 - x1
                height = y2 - y1
                
                # 过滤逻辑：忽略占据画面 90% 以上的异常大框（通常是误报或过近）
                if width >= (FRAME_WIDTH * 0.9) or height >= (FRAME_HEIGHT * 0.9):
                    continue
                
                # 如果通过过滤,认为本帧发现了有效目标
                current_frame_target_valid = True

                # 计算中心点
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2
                
                # 在画面上绘制标识
                cv2.rectangle(annotated_frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                cv2.circle(annotated_frame, (int(center_x), int(center_y)), 5, (0, 0, 255), -1)

        # --- 核心控制逻辑：0.8s 延迟判断 ---
        if current_frame_target_valid:
            if first_detected_time is None:
                # 目标首次出现,开始计时
                first_detected_time = time.time()
            
            # 计算目标已持续存在的时间
            duration = time.time() - first_detected_time
            
            if duration >= DELAY_THRESHOLD:
                if not buzzer_active.is_set():
                    print(f">>> [告警] 目标持续存在 {duration:.2f}s,开启蜂鸣器")
                    buzzer_active.set()
            else:
                # 目标存在但时间未满 0.8s,保持静默状态
                pass
        else:
            # 一旦目标在画面中消失,立即重置计时器并关闭蜂鸣器
            if first_detected_time is not None:
                print(">>> 目标消失,重置计时器")
                first_detected_time = None
            
            if buzzer_active.is_set():
                buzzer_active.clear()

        # 显示画面（将原始高分辨率画面缩小显示,节省显示开销）
        display_frame = cv2.resize(annotated_frame, (820, 616))
        cv2.imshow("Detection - Pi5", display_frame)

        # 按 'q' 退出
        if cv2.waitKey(1) == ord("q"):
            break

finally:
    # 释放资源
    print("\n正在关闭程序并清理环境...")
    buzzer_active.clear()
    picam2.stop()
    cv2.destroyAllWindows()
    GPIO.cleanup()