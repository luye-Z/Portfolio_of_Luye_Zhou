import cv2
import time
from picamera2 import Picamera2
from ultralytics import YOLO
from rpi_hardware_pwm import HardwarePWM

# =============================================================================
# GPIO 初始化
# =============================================================================


# =============================================================================
# 1. 硬件配置部分
# =============================================================================

# 创建Picamera2相机实例，用于控制树莓派摄像头
picam2 = Picamera2()

# 创建预览配置，设置摄像头输出参数
# main: 主流配置（用于图像处理）
# size: 图像分辨率设置为
# format: 图像格式设置为RGB888（24位RGB颜色）
SCREEN_WIDTH = 864
SCREEN_HEIGHT = 640
config = picam2.create_preview_configuration(main={
    "size": (SCREEN_WIDTH, SCREEN_HEIGHT),
    "format": "RGB888"
})

# 将配置应用到摄像头
picam2.configure(config)

# 启动摄像头，开始捕获图像
picam2.start()

# =============================================================================
# 2. 模型加载部分
# =============================================================================

# 加载YOLO目标检测模型
# 使用NCNN格式模型，适合在嵌入式设备上高效运行
# task='detect': 指定任务类型为目标检测
model = YOLO("/home/pi/projects/yolo26/model_folder/ncnn_format_model/640_imgsz_ncnn_model/0207_quadcopter_yolo26_ncnn_model", task='detect')

# =============================================================================
# 3. 舵机控制配置
# =============================================================================



# 舵机控制参数
# DEG_PER_PIX: 每像素对应的角度（度/像素）
# 假设摄像头视野为77度，则每像素对应 77 / 屏幕宽度 度
DEG_PER_PIX = 77.0 / SCREEN_WIDTH

# Kp_PAN 和 Kp_TILT: 比例控制系数（Proportional gain）
# 用于控制舵机响应速度，值越大响应越快，但可能产生震荡
# 建议范围：0.2 - 0.8，新手建议使用 0.4
Kp_PAN = 0.4    # 水平舵机（pan）的比例系数
Kp_TILT = 0.4   # 垂直舵机（tilt）的比例系数

# DEAD_ZONE_X 和 DEAD_ZONE_Y: 死区参数（像素）
# 当目标在死区范围内时，舵机不移动，避免抖动
# 建议范围：5 - 20，新手建议使用 10
DEAD_ZONE_X = 10   # 水平方向死区（像素）
DEAD_ZONE_Y = 10   # 垂直方向死区（像素）

# 舵机角度范围（度）
# 舵机可旋转的最小和最大角度
SERVO_MIN = -90   # 最小角度（向左/向上旋转90度）
SERVO_MAX = 90    # 最大角度（向右/向下旋转90度）

# 初始化舵机硬件
# HardwarePWM: 硬件PWM控制库，用于控制舵机
# pwm_channel: PWM通道号（0和1对应树莓派的两个PWM输出）
# hz=50: PWM频率为50Hz（舵机标准频率）
# chip=0: 使用PWM芯片0（树莓派5的默认配置）
servo_pan = HardwarePWM(pwm_channel=0, hz=50, chip=0)   # 水平舵机（左右旋转）
servo_tilt = HardwarePWM(pwm_channel=1, hz=50, chip=0)  # 垂直舵机（上下旋转）

# 启动舵机PWM信号
# start(): 启动PWM输出
# 7.5: 初始占空比，对应舵机中间位置（0度）
# 12.5: 初始占空比，对应舵机向上90度位置
servo_pan.start(7.5)    # 水平舵机启动在中间位置（0度）
servo_tilt.start(12.5)  # 垂直舵机启动在向上90度位置

# 初始化舵机角度变量
# 记录当前舵机角度，用于后续计算
servo_pan_angle = 0.0    # 水平舵机当前角度（度）
servo_tilt_angle = 90.0  # 垂直舵机当前角度（度）

# =============================================================================
# 4. 舵机控制函数
# =============================================================================

def set_servo_angle(pwm_obj, angle):
    """
    设置舵机角度
    
    参数说明:
    - pwm_obj: 舵机PWM对象（servo_pan 或 servo_tilt）
    - angle: 目标角度（度），范围在 SERVO_MIN 到 SERVO_MAX 之间
    
    功能说明:
    1. 将角度限制在安全范围内（-90度到90度）
    2. 将角度转换为PWM占空比（2.5%到12.5%）
    3. 通过PWM信号控制舵机旋转到指定角度
    
    PWM占空比计算公式:
    duty = (angle + 90) * (10 / 180) + 2.5
    - angle + 90: 将-90~90度映射到0~180度
    - 10 / 180: 将0~180度映射到0~10%
    - + 2.5: 将0~10%映射到2.5%~12.5%（舵机标准范围）
    """
    # 限制角度在安全范围内，防止舵机损坏
    angle = max(SERVO_MIN, min(SERVO_MAX, angle))
    
    # 将角度转换为PWM占空比（2.5% - 12.5%）
    duty = (angle + 90) * (10 / 180) + 2.5
    
    # 设置舵机PWM占空比，控制舵机旋转
    pwm_obj.change_duty_cycle(duty)

# =============================================================================
# 5. 性能指标初始化
# =============================================================================

# 初始化性能统计变量
frame_counts = 0              # 处理的帧数计数器
total_inference_time = 0      # 总推理时间（毫秒）
total_preprocess_time = 0     # 总预处理时间（毫秒）
total_postprocess_time = 0    # 总后处理时间（毫秒）
session_start_time = time.time()  # 记录会话开始时间

# 打印启动信息，提示用户如何退出程序
print("Streaming started... Press 'q' to quit and view Performance Report.")
print("Servo tracking enabled: Camera will follow detected targets")

# =============================================================================
# 6. 主循环 - 实时目标检测与舵机追踪
# =============================================================================

try:
    # 无限循环，持续进行目标检测和舵机追踪
    while True:
        # 从摄像头捕获一帧图像
        # capture_array(): 返回numpy数组格式的图像数据
        frame = picam2.capture_array()
        
        # 执行YOLO目标检测推理
        # frame: 输入图像
        # imgsz=640: 推理时将图像缩放到640x640
        # conf=0.25: 置信度阈值，只显示置信度大于25%的检测结果
        # verbose=False: 禁用详细输出，减少控制台信息
        results = model(frame, imgsz=640, conf=0.25, verbose=False)

        # 从Ultralytics内部字典中累积时间统计（单位：毫秒）
        # speed字典包含：preprocess（预处理）、inference（推理）、postprocess（后处理）
        speed = results[0].speed
        total_preprocess_time += speed['preprocess']      # 累加预处理时间
        total_inference_time += speed['inference']        # 累加推理时间
        total_postprocess_time += speed['postprocess']    # 累加后处理时间
        frame_counts += 1                                 # 帧数计数器加1

        # 计算实时FPS（帧率）用于显示
        # latency_ms: 单帧总延迟时间（预处理+推理+后处理）
        # rt_fps: 实时帧率 = 1000毫秒 / 总延迟时间
        latency_ms = sum(speed.values())
        rt_fps = 1000 / latency_ms if latency_ms > 0 else 0
        
        # 使用原始帧进行绘制，避免plot()方法的开销
        annotated_frame = frame.copy()
        
        # 初始化目标追踪变量
        current_frame_valid = False  # 当前帧是否检测到有效目标
        target_x, target_y = None, None  # 目标中心坐标
        confidence = 0.0  # 目标置信度

        # 查找第一个有效的检测结果并使用OpenCV绘制
        for box in results[0].boxes:
            # 获取检测框坐标
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            w, h = x2 - x1, y2 - y1  # 计算检测框宽度和高度
            confidence = box.conf[0].item()  # 获取置信度

            # 过滤过大的检测框（可能是误检或目标太近）
            # 如果检测框超过屏幕的70%，则跳过
            if w >= (SCREEN_WIDTH * 0.7) or h >= (SCREEN_HEIGHT * 0.7):
                continue

            # 标记当前帧有效
            current_frame_valid = True
            
            # 计算目标中心坐标
            target_x = (x1 + x2) / 2  # 水平中心
            target_y = (y1 + y2) / 2  # 垂直中心

            # 使用OpenCV绘制检测框（绿色边界框）
            cv2.rectangle(annotated_frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
            
            # 绘制目标中心点（红色圆点）
            cv2.circle(annotated_frame, (int(target_x), int(target_y)), 5, (0, 0, 255), -1)
            
            # 绘制置信度标签（黄色文字）
            label = f"Conf: {confidence*100:.1f}%"
            cv2.putText(annotated_frame, label, 
                        (int(x1), int(y1)-10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

            # 只处理第一个有效目标，避免多个目标干扰
            break

        # =============================================================================
        # 7. 舵机追踪逻辑
        # =============================================================================
        
        # 如果检测到有效目标，则进行舵机追踪
        if current_frame_valid:
            # 计算目标相对于屏幕中心的误差（像素）
            # 正值表示目标在中心右侧/下方，负值表示在左侧/上方
            error_x = target_x - (SCREEN_WIDTH / 2)   # 水平误差
            error_y = target_y - (SCREEN_HEIGHT / 2) # 垂直误差

            # 水平舵机（pan）控制
            # 只有当误差超过死区时才调整舵机，避免抖动
            if abs(error_x) > DEAD_ZONE_X:
                # 计算目标角度变化量（度）
                # 公式：角度变化 = 误差像素 × 每像素角度 × 比例系数
                angle_change = (error_x * DEG_PER_PIX) * Kp_PAN
                
                # 更新舵机角度（注意：水平舵机方向相反，需要减去角度变化）
                servo_pan_angle -= angle_change
                
                # 限制角度在安全范围内
                servo_pan_angle = max(SERVO_MIN, min(SERVO_MAX, servo_pan_angle))
                
                # 控制舵机旋转到新角度
                set_servo_angle(servo_pan, servo_pan_angle)

            # 垂直舵机（tilt）控制
            # 只有当误差超过死区时才调整舵机，避免抖动
            if abs(error_y) > DEAD_ZONE_Y:
                # 计算目标角度变化量（度）
                # 公式：角度变化 = 误差像素 × 每像素角度 × 比例系数
                angle_change = (error_y * DEG_PER_PIX) * Kp_TILT
                
                # 更新舵机角度（垂直舵机方向正常，加上角度变化）
                servo_tilt_angle += angle_change
                
                # 限制角度在安全范围内
                servo_tilt_angle = max(SERVO_MIN, min(SERVO_MAX, servo_tilt_angle))
                
                # 控制舵机旋转到新角度
                set_servo_angle(servo_tilt, servo_tilt_angle)

        # 在图像上绘制实时FPS信息
        # (30, 60): 文字位置（左上角）
        # cv2.FONT_HERSHEY_SIMPLEX: 字体类型
        # 1.5: 字体大小
        # (0, 255, 0): 颜色（绿色）
        # 3: 线条粗细
        cv2.putText(annotated_frame, f"FPS: {rt_fps:.1f}", (30, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)

        # 显示检测结果窗口
        # 将图像缩放到820x616以适应屏幕显示
        # "YOLO NCNN Detection": 窗口标题
        display_frame = cv2.resize(annotated_frame, (820, 616))
        
        # 绘制死区可视化（黄色矩形框）
        # 死区表示舵机不响应的区域，避免抖动
        cv_dz_x = int(DEAD_ZONE_X * (820 / SCREEN_WIDTH))   # 缩放后的水平死区
        cv_dz_y = int(DEAD_ZONE_Y * (616 / SCREEN_HEIGHT))  # 缩放后的垂直死区
        cv2.rectangle(display_frame, 
                      (410 - cv_dz_x, 308 - cv_dz_y),   # 左上角坐标
                      (410 + cv_dz_x, 308 + cv_dz_y),   # 右下角坐标
                      (255, 255, 0), 1)                  # 黄色线条，粗细为1
        
        # 显示舵机角度信息
        cv2.putText(display_frame, f"Pan: {servo_pan_angle:.1f}°", (10, 90), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.putText(display_frame, f"Tilt: {servo_tilt_angle:.1f}°", (10, 110), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        cv2.imshow("YOLO NCNN Detection with Servo Tracking", display_frame)

        # 检测按键输入
        # waitKey(1): 等待1毫秒的按键输入
        # ord("q"): 按下'q'键时返回ASCII码值
        if cv2.waitKey(1) == ord("q"):
            break  # 退出循环

# =============================================================================
# 8. 性能分析报告（程序退出时执行）
# =============================================================================

finally:
    # 记录会话结束时间
    session_end_time = time.time()
    # 计算总运行时长（秒）
    total_duration = session_end_time - session_start_time
    
    # 如果至少处理了一帧，则生成性能报告
    if frame_counts > 0:
        # 计算各阶段的平均时间
        avg_pre = total_preprocess_time / frame_counts      # 平均预处理时间
        avg_inf = total_inference_time / frame_counts        # 平均推理时间
        avg_post = total_postprocess_time / frame_counts    # 平均后处理时间
        avg_total_latency = avg_pre + avg_inf + avg_post    # 平均总延迟时间
        avg_fps = frame_counts / total_duration             # 平均帧率

        # 打印性能报告标题
        print("\n" + "="*40)
        print("🚀 YOLO NCNN PERFORMANCE REPORT")
        print("="*40)
        
        # 打印基本统计信息
        print(f"Total Frames Processed:  {frame_counts}")           # 处理的总帧数
        print(f"Total Session Duration: {total_duration:.2f} s")    # 总运行时长
        print("-" * 40)
        
        # 打印各阶段平均耗时（保留22位小数，精确到微秒级）
        print(f"Avg Preprocess:         {avg_pre:.22f} ms")         # 平均预处理时间
        print(f"Avg Inference:          {avg_inf:.22f} ms")         # 平均推理时间
        print(f"Avg Postprocess:        {avg_post:.22f} ms")        # 平均后处理时间
        print(f"Avg Total Latency:      {avg_total_latency:.22f} ms")  # 平均总延迟
        print("-" * 40)
        
        # 打印平均帧率
        print(f"AVG PIPELINE FPS:       {avg_fps:.2f}")              # 平均流水线帧率
        
        # 瓶颈分析：判断主要性能瓶颈
        # 如果推理时间大于（预处理+后处理）时间，则瓶颈在神经网络推理（CPU受限）
        # 否则瓶颈在图像I/O或渲染
        if avg_inf > (avg_pre + avg_post):
            bottleneck = "Neural Network Inference (CPU bound)"
        else:
            bottleneck = "Image I/O or Rendering"
        print(f"Primary Bottleneck:     {bottleneck}")               # 主要性能瓶颈
        print("="*40)

    # =============================================================================
    # 9. 资源清理
    # =============================================================================
    
    print("\n正在释放资源...")
    
    # 将舵机复位到初始位置
    # 水平舵机复位到0度（中间位置）
    # 垂直舵机复位到90度（向上位置）
    set_servo_angle(servo_pan, 0)
    set_servo_angle(servo_tilt, 90)
    
    # 等待舵机完成复位动作
    time.sleep(1.5)
    
    # 停止舵机PWM信号
    servo_pan.stop()
    servo_tilt.stop()
    
    # 停止摄像头
    picam2.stop()
    
    # 关闭所有OpenCV窗口
    cv2.destroyAllWindows()
    
    print("资源释放完成！")