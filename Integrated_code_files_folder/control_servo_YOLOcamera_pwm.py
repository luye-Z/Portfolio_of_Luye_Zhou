import cv2
from picamera2 import Picamera2
from ultralytics import YOLO
from gpiozero import AngularServo
from time import sleep, time  # 引入 time 用于非阻塞延时
import sys
from rpi_hardware_pwm import HardwarePWM


#——————————————————————————————YOLO相机初始化部分————————————————————————
#-----------------------------------------------------------------------
#———————————————————————————————————————————————————————————————————————

# --- 0. 定义分辨率常量 ---
SCREEN_WIDTH = 1640
SCREEN_HEIGHT = 1232


DEG_PER_PIX = 77.0 / SCREEN_WIDTH  # 约为 0.047
# 1. Hardware Configuration
picam2 = Picamera2()
config = picam2.create_preview_configuration(main={
    "size": (SCREEN_WIDTH, SCREEN_HEIGHT), 
    "format": "RGB888"
})
picam2.configure(config)
picam2.start()

# Load NCNN Model
model = YOLO("yolo26n_01_24_quadcopter_best_ncnn_model", task='detect')

print("Streaming started... Press 'q' to quit.")
#-----------------------------------------------------------------------



#——————————————————————————————servo初始化部分———————————————————————————
#-----------------------------------------------------------------------
#———————————————————————————————————————————————————————————————————————

# --- 硬件配置 ---
# 根据你的 ls 结果：1f00098000 对应 pwmchip0
CHIP_ID = 0  

# GPIO 12 -> PWM0_CHAN0 -> channel 0 (TILT 轴)
# GPIO 13 -> PWM0_CHAN1 -> channel 1 (PAN 轴)
TILT_CHANNEL = 0
PAN_CHANNEL = 1
print(f"正在初始化硬件 PWM (Chip {CHIP_ID})...")

# 初始化两个通道
servo_tilt = HardwarePWM(pwm_channel=TILT_CHANNEL, hz=50, chip=CHIP_ID)
servo_pan = HardwarePWM(pwm_channel=PAN_CHANNEL, hz=50, chip=CHIP_ID)

# 启动，初始占空比 7.5% (对应 0度)
servo_tilt.start(7.5)
servo_pan.start(7.5)


print("硬件PWM初始化成功")
#定义舵机运动角度范围
SERVO_PAN_ANGLE_MAX = 89
SERVO_PAN_ANGLE_MIN = -89
SERVO_TILT_ANGLE_MAX = 89
SERVO_TILT_ANGLE_MIN = -89

#定义两个全局变量用来储存舵机当前的运动角度
servo_pan_current_angle = 0
servo_tilt_current_angle = 0


#舵机角度位置安全检验
def secure_servo_pan_angle(angle):
    if angle < SERVO_PAN_ANGLE_MIN:
        angle = SERVO_PAN_ANGLE_MIN 
    elif angle > SERVO_PAN_ANGLE_MAX:
        angle = SERVO_PAN_ANGLE_MAX
    return angle

def secure_servo_tilt_angle(angle):
    if angle < SERVO_TILT_ANGLE_MIN:
        angle = SERVO_TILT_ANGLE_MIN
    elif angle > SERVO_TILT_ANGLE_MAX:
        angle = SERVO_TILT_ANGLE_MAX
    return angle

def set_angle(pwm_obj, angle):
    """将角度(-90到90)映射为硬件占空比(2.5到12.5)"""
    angle = max(-90, min(90, angle))
    duty = (angle + 90) * (10 / 180) + 2.5
    pwm_obj.change_duty_cycle(duty)
    
# set_angle(servo_pan, angle)
#设置舵机初始化位置
set_angle(servo_pan, servo_pan_current_angle)
set_angle(servo_tilt, servo_tilt_current_angle)
print(f"舵机初始化位置设置完成")
print(f"舵机初始化位置:  pan={servo_pan_current_angle}°, tilt={servo_tilt_current_angle}°")

sleep(0.66)

# #暂时释放舵机控制引脚，防止舵机抖动
# servo_pan.value = None
# servo_tilt.value = None

# --- 新增：时间控制变量 舵机控制时间戳，限制舵机控制速度 ---
# last_servo_update_time = 0
# SERVO_UPDATE_INTERVAL = 1  # 限制舵机
# 舵机调整冷却时间控制
is_adjusting = False
last_adjust_time = 0
COOLDOWN_TIME = 0.1  # 冷却时间 0.5秒

#-----------------------------------------------------------------------
try:
    while True:
        # --- 1. 只有不在调整时，才进行采样和推理 ---
        if not is_adjusting:
            # Capture frame
            frame = picam2.capture_array()
            
            # Inference
            results = model(frame, imgsz=320, conf=0.25, verbose=False)
            
            annotated_frame = frame.copy() 

            object_detected = False #标志位 
            
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    # 获取坐标
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    
                    # 计算目标大小
                    width = x2 - x1
                    height = y2 - y1
                    
                    # --- 过滤逻辑 ---
                    # 如果宽度 或 高度 超过了画面的 90%，则忽略
                    if width >= (SCREEN_WIDTH * 0.9) or height >= (SCREEN_HEIGHT * 0.9):
                        continue

                    # --- 核心修改：改为计算中心坐标 ---
                    center_x = (x1 + x2) / 2
                    center_y = (y1 + y2) / 2  # 修改处：现在计算的是垂直方向的中心点
                    
                    object_detected = True
                    # 打印中心坐标
                    print(f"检测到有效物体: 中心坐标: ({center_x:.0f}, {center_y:.0f}) | 尺寸({width:.0f}x{height:.0f})")

                    # --- 手动绘制 ---
                    # 1. 画检测框 (绿色)
                    cv2.rectangle(annotated_frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                    
                    # 2. 画中心点 (红色圆圈) -> 修改处：位置改为 (center_x, center_y)
                    cv2.circle(annotated_frame, (int(center_x), int(center_y)), 5, (0, 0, 255), -1)
                    
                    # 3. 写标签
                    cv2.putText(annotated_frame, f"Center", (int(center_x)-20, int(center_y)-10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                    
                    #涉及舵机控制相关
                    # 计算物体相对于屏幕中心的偏移
                    # current_time = time()
                    
                    # 2. 只有当距离上次更新超过一定时间 (比如0.05秒)，才允许发送舵机指令
                    #    这起到了 sleep 的作用，但不会卡住画面
                    # if current_time - last_servo_update_time > SERVO_UPDATE_INTERVAL:
                    object_x_pos_offset = center_x - SCREEN_WIDTH / 2
                    object_y_pos_offset = center_y - SCREEN_HEIGHT / 2
                    # last_servo_update_time = current_time  # 更新最后控制时间戳
                    
                    
                    print(f"物体相对于屏幕中心X轴方向的偏移: {object_x_pos_offset:.0f}")
                    
                    OFFSET_ADJUST_STEP = 1
                    # P = 0.00005 
                    if abs(object_x_pos_offset) > 100:
                        
                        # if object_x_pos_offset > 100:  # 物体在屏幕右侧
                            #舵机度数减小
                            #舵机度数减小去追物体
                            
                            #这行代码才是正式执行的代码，将舵机角度设置为安全角度
                            
                            servo_pan_current_angle = secure_servo_pan_angle(servo_pan_current_angle - (object_x_pos_offset * DEG_PER_PIX))
                            # servo_pan.angle = secure_servo_pan_angle(servo_pan_current_angle)
                            set_angle(servo_pan, servo_pan_current_angle)
                            is_adjusting=True
                            last_adjust_time = time()
                            
                        # elif object_x_pos_offset < -100:  # 物体在屏幕左侧
                        #     #舵机度数增大
                        #     servo_pan_current_angle = secure_servo_pan_angle(servo_pan_current_angle -(object_x_pos_offset * DEG_PER_PIX))
                        #     servo_pan.angle = secure_servo_pan_angle(servo_pan_current_angle)
            if not object_detected:
                print("未检测到目标物体，正在等待目标...")           
                #暂时释放舵机控制引脚，防止舵机抖动
                servo_pan.value = None
                servo_tilt.value = None        

            # Display
            cv2.imshow("YOLO NCNN Detection", cv2.resize(annotated_frame, (820, 616)))

            if cv2.waitKey(1) == ord("q"):
                break
        else:
            if is_adjusting and time() - last_adjust_time > 0.5:
                is_adjusting = False
                servo_pan.value = None
finally:
    picam2.stop()
    cv2.destroyAllWindows()