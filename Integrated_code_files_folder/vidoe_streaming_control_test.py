import cv2
from picamera2 import Picamera2
from ultralytics import YOLO
from rpi_hardware_pwm import HardwarePWM
from time import sleep
import sys

# —————————————————————————————— 配置区域 ——————————————————————————————
# 1. 屏幕与FOV配置
SCREEN_WIDTH = 1640
SCREEN_HEIGHT = 1232
# DEG_PER_PIX: 像素转角度的比例。
# 如果追踪反应太慢，可以稍微调大这个值；如果震荡，调小这个值。
DEG_PER_PIX = 77.0 / SCREEN_WIDTH  

# 2. 舵机平滑控制参数 (核心修改)
# Kp (比例系数): 范围 0.0 ~ 1.0
# 0.1 表示每帧只修正 10% 的误差，动作很慢但很滑。
# 0.5 表示每帧修正 50% 的误差，动作快但可能有点冲。
# 建议从 0.15 开始调试
Kp_PAN = 0.2
Kp_TILT = 0.15

# 死区 (Dead Zone): 目标偏离中心多少像素内不移动舵机
# 防止舵机在目标静止时因为微小的检测波动而滋滋响
DEAD_ZONE_X = 40
DEAD_ZONE_Y = 40

# 舵机范围
SERVO_PAN_ANGLE_MAX = 89
SERVO_PAN_ANGLE_MIN = -89
SERVO_TILT_ANGLE_MAX = 89
SERVO_TILT_ANGLE_MIN = -89

# —————————————————————————————— 硬件初始化 ——————————————————————————————

# 1. 相机初始化
print("正在初始化相机...")
picam2 = Picamera2()
config = picam2.create_preview_configuration(main={
    "size": (SCREEN_WIDTH, SCREEN_HEIGHT), 
    "format": "RGB888"
})
picam2.configure(config)
picam2.start()

# 2. 模型加载
print("正在加载 YOLO 模型...")
model = YOLO("yolo26n_01_24_quadcopter_best_ncnn_model", task='detect')

# 3. 舵机初始化
CHIP_ID = 0  
TILT_CHANNEL = 0
PAN_CHANNEL = 1

print(f"正在初始化硬件 PWM (Chip {CHIP_ID})...")
servo_tilt = HardwarePWM(pwm_channel=TILT_CHANNEL, hz=50, chip=CHIP_ID)
servo_pan = HardwarePWM(pwm_channel=PAN_CHANNEL, hz=50, chip=CHIP_ID)

servo_tilt.start(7.5) # 0度
servo_pan.start(7.5)  # 0度

# 全局角度变量
servo_pan_current_angle = 0
servo_tilt_current_angle = 0

# —————————————————————————————— 功能函数 ——————————————————————————————

def set_angle(pwm_obj, angle):
    """将角度(-90到90)映射为硬件占空比(2.5到12.5)"""
    # 限制物理角度范围
    angle = max(-90, min(90, angle))
    duty = (angle + 90) * (10 / 180) + 2.5
    pwm_obj.change_duty_cycle(duty)

def secure_servo_pan_angle(angle):
    return max(SERVO_PAN_ANGLE_MIN, min(SERVO_PAN_ANGLE_MAX, angle))

def secure_servo_tilt_angle(angle):
    return max(SERVO_TILT_ANGLE_MIN, min(SERVO_TILT_ANGLE_MAX, angle))

# 初始化位置
set_angle(servo_pan, servo_pan_current_angle)
set_angle(servo_tilt, servo_tilt_current_angle)
sleep(1.0) # 等待归位
print("系统就绪，开始推流...")

# —————————————————————————————— 主循环 ——————————————————————————————
try:
    while True:
        # 1. 获取画面
        frame = picam2.capture_array()
        
        # 2. 推理 (imgsz越小速度越快，320是一个很好的平衡点)
        results = model(frame, imgsz=320, conf=0.25, verbose=False)
        
        annotated_frame = frame.copy() 
        object_detected = False 
        
        # 最佳目标数据容器
        best_target_center_x = None
        best_target_center_y = None
        
        # 3. 解析结果
        # 简单起见，我们假设只追踪 conf 最高的或者列表里的第一个符合条件的目标
        for result in results:
            boxes = result.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                
                # 计算尺寸
                width = x2 - x1
                height = y2 - y1
                
                # 过滤过大的误检 (占屏幕90%以上)
                if width >= (SCREEN_WIDTH * 0.9) or height >= (SCREEN_HEIGHT * 0.9):
                    continue

                # 计算中心
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2
                
                # 绘制UI
                cv2.rectangle(annotated_frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                cv2.circle(annotated_frame, (int(center_x), int(center_y)), 5, (0, 0, 255), -1)
                cv2.putText(annotated_frame, f"Tgt", (int(x1), int(y1)-10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

                # 只要检测到一个有效目标，就标记并跳出循环(单目标追踪)
                # 如果你想追踪最大的目标，可以在这里加逻辑比较面积
                object_detected = True
                best_target_center_x = center_x
                best_target_center_y = center_y
                break # 暂时只处理第一个检测到的物体
            
            if object_detected:
                break

        # 4. 舵机平滑追踪逻辑
        if object_detected and best_target_center_x is not None:
            # 计算偏移量 (Error)
            error_x = best_target_center_x - (SCREEN_WIDTH / 2)
            error_y = best_target_center_y - (SCREEN_HEIGHT / 2) # 如果需要Tilt轴，同理

            # --- PAN (左右) 轴控制 ---
            if abs(error_x) > DEAD_ZONE_X:
                # 核心算法：当前角度 - (误差 * 像素角度比 * 柔和系数)
                # 注意正负号：如果物体在右边(error_x > 0)，我们需要减小角度往右转(取决于你的舵机安装方向)
                # 如果发现反了，把下面的减号改成加号
                
                delta_angle = (error_x * DEG_PER_PIX) * Kp_PAN
                
                # 更新目标角度
                servo_pan_current_angle -= delta_angle
                
                # 安全限制
                servo_pan_current_angle = secure_servo_pan_angle(servo_pan_current_angle)
                
                # 执行动作
                set_angle(servo_pan, servo_pan_current_angle)
                
                print(f"追踪中... 偏移:{error_x:.0f} -> 修正:{delta_angle:.2f}°")
            
            # --- TILT (上下) 轴控制 (如果需要可取消注释) ---
            if abs(error_y) > DEAD_ZONE_Y:
                delta_angle_y = (error_y * DEG_PER_PIX) * Kp_TILT
                # 注意Y轴方向通常和图像坐标系是反的或者正的，需要测试
                servo_tilt_current_angle += delta_angle_y 
                servo_tilt_current_angle = secure_servo_tilt_angle(servo_tilt_current_angle)
                set_angle(servo_tilt, servo_tilt_current_angle)

        else:
            # 未检测到目标时
            # 这里的策略是：保持当前位置不动，或者你可以写代码让它自动回中
            pass

        # 5. 显示画面
        # 缩小一点显示以减少CPU负载
        display_frame = cv2.resize(annotated_frame, (820, 616))
        # 画出中心死区框，方便调试
        cv2.rectangle(display_frame, 
                      (int(410 - DEAD_ZONE_X/2), int(308 - DEAD_ZONE_Y/2)), 
                      (int(410 + DEAD_ZONE_X/2), int(308 + DEAD_ZONE_Y/2)), 
                      (255, 255, 0), 1)
        
        cv2.imshow("Continuous Tracking", display_frame)

        if cv2.waitKey(1) == ord("q"):
            break

finally:
    # 清理资源
    print("正在关闭...")
    picam2.stop()
    servo_pan.stop()
    servo_tilt.stop()
    cv2.destroyAllWindows()