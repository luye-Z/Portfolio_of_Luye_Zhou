import cv2
import time
from yolo_predict import YOLODetector
from system_manager import SystemManager
import os
import csv
from datetime import datetime


#main函数测试版 ，主要功能，是创建一个runing_code 函数 ，去实现各种功能逻辑的调用
def cv_show(frame, results, sys):
    """
    极简显示函数：针对树莓派深度优化版
    """
    # [核心优化 1]：零拷贝 (Zero-copy) 原则
    # 移除 frame.copy()，直接在原图上绘制。如果其他环节不需要纯净帧，这是最省内存带宽的做法。
    annotated_frame = frame 
    
    # 1. 确保结果不为空
    if len(results) == 0 or len(results[0].boxes) == 0:
        cv2.imshow("YOLO Detection", annotated_frame)
    else:
        # [核心优化 2]：将张量一次性推入 CPU 并转为 NumPy 数组
        # 避免在 for 循环中反复调用 .tolist() 和 .item()，大幅减少 Python 解释器与底层 C++ 的通信开销
        boxes = results[0].boxes
        xyxy_array = boxes.xyxy.cpu().numpy()
        conf_array = boxes.conf.cpu().numpy()
        cls_array = boxes.cls.cpu().numpy()
        
        # [核心优化 3]：将常量计算提至循环外，避免在每一次目标检测时重复计算浮点乘法
        max_w = sys.detector.SCREEN_WIDTH * 0.55
        max_h = sys.detector.SCREEN_HEIGHT * 0.55
        
        # 2. 绘制检测框
        for i in range(len(xyxy_array)):
            # 直接从 NumPy 数组中解包，速度极快
            x1, y1, x2, y2 = xyxy_array[i]
            conf = conf_array[i]
            cls = int(cls_array[i])
            
            w, h = x2 - x1, y2 - y1
            
            # 过滤逻辑
            if w >= max_w or h >= max_h:
                continue
            
            # 统一转为整型坐标，供 OpenCV 绘制使用
            ix1, iy1, ix2, iy2 = int(x1), int(y1), int(x2), int(y2)
            
            # 画矩形框
            cv2.rectangle(annotated_frame, (ix1, iy1), (ix2, iy2), (0, 255, 0), 2)
            
            # 简易标签
            label = f"ID:{cls} {conf:.2f}"
            cv2.putText(annotated_frame, label, (ix1, iy1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # 显示带框图像
        cv2.imshow("YOLO Detection", annotated_frame)
    
    # 3. 退出逻辑：按 'q' 键退出
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        return True
    
    return False

def pid_control_servos(sys,obj_target_center_x,obj_target_center_y, kp_pan=0.35, kp_tilt=0.30, kd_pan=0.15, kd_tilt=0.12):
    #工具函数，根据YOLO检测到的目标位置，更新舵机跟踪角度
    # 调用舵机控制器跟踪目标
        #直接从detector类里面获取目标中心坐标,yolo_predict.py文件里面定义的这个类，只有这一个类
        
        # obj_target_center_x, obj_target_center_y = sys.detector.get_target_center()
        # 调用 PID 控制器计算角度
        
        #为了给予每种模式不同的PID参数，在这里添加PID参数更新函数
        sys.pid_controller.pid_parameters_update(kp_pan, kp_tilt, kd_pan, kd_tilt)
        
        sys.pid_controller.pid_control_calculate(
            obj_target_center_x, 
            obj_target_center_y
        )
         # 获取 PID 控制器输出
        pan_controller_output, tilt_controller_output = sys.pid_controller.get_PID_controller_output()
        #控制舵机运动
        sys.servo_controller.set_pan_angle(pan_controller_output)
        sys.servo_controller.set_tilt_angle(tilt_controller_output)
        
def update_servo_tracking_add_feedforward(sys, kp_pan=0.35, kp_tilt=0.30, kd_pan=0.15, kd_tilt=0.12, Kff_pan=0.05, Kff_tilt=0.04):    
    #工具函数，根据YOLO检测到的目标位置，更新舵机跟踪角度
    # 调用舵机控制器跟踪目标
        #直接从detector类里面获取目标中心坐标,yolo_predict.py文件里面定义的这个类，只有这一个类
        
        obj_target_center_x, obj_target_center_y = sys.detector.get_target_center()
        # 调用 PID 控制器计算角度
        
        #为了给予每种模式不同的PID参数，在这里添加PID参数更新函数
        sys.pid_controller.pid_parameters_update(kp_pan, kp_tilt, kd_pan, kd_tilt)
        sys.pid_controller.pid_feedforward_parameters_update(Kff_pan, Kff_tilt)
        
        
        sys.pid_controller.pid_control_calculate(obj_target_center_x, obj_target_center_y)
        sys.pid_controller.feed_forward_control_calculate(obj_target_center_x, obj_target_center_y)
         
         # 获取 PID 控制器输出
        pan_controller_output, tilt_controller_output = sys.pid_controller.get_PID_controller_output()
        #控制舵机运动
        sys.servo_controller.set_pan_angle(pan_controller_output)
        sys.servo_controller.set_tilt_angle(tilt_controller_output)
        
def program_mode_yolo_detection(sys , activate_buzzer=True,activate_screen_show=False): #添加了参数控制，可以控制是否开启蜂鸣器和屏幕显示
    #YOLO检测模式，基础模式，不显示图像。
    
    annotated_frame = None
    result = None
            

    # YOLO 检测模式：调用 detect_frame
    print("YOLO 检测模式")
    
    # 调用 YOLO 检测（只调用一次！）
    result, annotated_frame = sys.detector.detect_frame()

    # 检查是否检测到目标
    #这里使用与操作符，是再次检测，确保当前模式是yolo detection\nno image，防止切换为菜单模式，蜂鸣器依旧鸣叫
    if sys.detector.get_if_target_detected() and sys.get_program_mode() != "program menu":
        
        # 调用工具函数，更新舵机跟踪角度
        obj_target_center_x, obj_target_center_y = sys.detector.get_target_center()
        pid_control_servos(sys,obj_target_center_x,obj_target_center_y)
        

        #activate indicator led and buzzer
        sys.rgb_led.set_color_name("red")
        
        if activate_buzzer:
            sys.buzzer.start_alarm()
        
        
        current_d = sys.laser_sensor.distance
        print(f"激光测距距离: {current_d} mm")
        obj_target_center_x, obj_target_center_y = sys.detector.get_target_center()
        print(f"目标的中心坐标是({obj_target_center_x:.2f}, {obj_target_center_y:.2f})")
    else:
        print("未检测到目标")
        # 停止蜂鸣器报警
        sys.buzzer.stop_alarm()
        sys.rgb_led.set_color_name("green")
    

    
    if annotated_frame is not None and result is not None and activate_screen_show:
        cv_show(annotated_frame, result, sys)
        
def program_mode_kalman_test(sys , activate_buzzer=True,activate_screen_show=False): #添加了参数控制，可以控制是否开启蜂鸣器和屏幕显示

    #YOLO检测模式，基础模式，不显示图像。
    
    annotated_frame = None
    result = None
            

    # YOLO 检测模式：调用 detect_frame
    print("YOLO 检测模式")
    
    # 调用 YOLO 检测（只调用一次！）
    result, annotated_frame = sys.detector.detect_frame()

    # 检查是否检测到目标
    #这里使用与操作符，是再次检测，确保当前模式是yolo detection\nno image，防止切换为菜单模式，蜂鸣器依旧鸣叫
    if sys.detector.get_if_target_detected() and sys.get_program_mode() != "program menu":
        
        # 调用工具函数，更新舵机跟踪角度
        obj_target_center_x, obj_target_center_y = sys.detector.get_target_center()
        obj_target_kalman_adjust_center_x, obj_target_kalman_adjust_center_y = sys.kalman_tracker.update_and_output(obj_target_center_x, obj_target_center_y)
        pid_control_servos(sys,obj_target_kalman_adjust_center_x,obj_target_kalman_adjust_center_y)
        

        #activate indicator led and buzzer
        sys.rgb_led.set_color_name("red")
        
        if activate_buzzer:
            sys.buzzer.start_alarm()
        
        
        current_d = sys.laser_sensor.distance
        print(f"激光测距距离: {current_d} mm")
        obj_target_center_x, obj_target_center_y = sys.detector.get_target_center()
        print(f"目标的中心坐标是({obj_target_center_x:.2f}, {obj_target_center_y:.2f})")
    else:
        print("未检测到目标")
        # 停止蜂鸣器报警
        sys.buzzer.stop_alarm()
        sys.rgb_led.set_color_name("green")
    

    
    if annotated_frame is not None and result is not None and activate_screen_show:
        cv_show(annotated_frame, result, sys)

def program_mode_yolodetection_show(sys):
    program_mode_yolo_detection(sys , activate_buzzer=True,activate_screen_show=True)   

def program_mode_yolodetection_no_show_no_buzzer(sys):

    program_mode_yolo_detection(sys , activate_buzzer=False,activate_screen_show=False)
    
def program_mode_yolodetection_show_no_buzzer(sys):   
    program_mode_yolo_detection(sys , activate_buzzer=False,activate_screen_show=True)   



# def program_mode_draw_record_chart(sys):
#     """
#     绘制记录图表模式
#     基于 YOLO 检测模式，把每一次检测到的目标中心点坐标记录到文件中。
#     在当前路径下新建 detection_records 文件夹，按时间戳新建 CSV 文件。
#     """
    


def program_mode_draw_record_chart(sys):
    # 1. ========== 初始化记录文件路径 (CSV) ==========
    if not hasattr(sys, '_record_file_path') or sys._record_file_path is None:
        current_script_dir = os.path.dirname(os.path.abspath(__file__))
        record_dir = os.path.join(
            current_script_dir, 
            "detection_records_analyse", 
            "detection_records"
        )
        
        if not os.path.exists(record_dir):
            os.makedirs(record_dir)
            
        # 生成带日期和时间的文件名
        file_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data_record_{file_timestamp}.csv"
        sys._record_file_path = os.path.join(record_dir, filename)
        
        # 写入表头，增加 'timestamp' 列
        with open(sys._record_file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'target_x', 'target_y', 'error_x', 'error_y', 'pid_out_x', 'pid_out_y'])

    # 2. ========== 执行 YOLO 检测与控制 ==========
    program_mode_yolo_detection(sys, activate_buzzer=False, activate_screen_show=False)

    # 3. ========== 获取数据并写入 ==========
    try:
        # --- 获取当前行的时间戳 (时:分:秒.毫秒) ---
        now_time = datetime.now().strftime("%H:%M:%S.%f")[:-3] 

        # 获取原始数值
        target_center = sys.detector.get_target_center()
        t_x, t_y = target_center if target_center else (0.0, 0.0)
        
        p_out_x, p_out_y = sys.pid_controller.get_PID_controller_output()
        
        err_x = sys.pid_controller.error_x if hasattr(sys.pid_controller, 'error_x') else 0.0
        err_y = sys.pid_controller.error_y if hasattr(sys.pid_controller, 'error_y') else 0.0

        # 格式化数值精度
        values = [t_x, t_y, err_x, err_y, p_out_x, p_out_y]
        formatted_values = [f"{val:.3f}" for val in values]

        # 组合最终写入行：[时间, x, y, err_x, err_y, out_x, out_y]
        final_row = [now_time] + formatted_values

        with open(sys._record_file_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(final_row)
            
    except Exception as e:
        print(f"写入记录失败: {e}")




def program_mode_feedforward_control_test(sys , activate_buzzer=True,activate_screen_show=False):
    #YOLO检测模式，基础模式，不显示图像。
    
    annotated_frame = None
    result = None
            

    # YOLO 检测模式：调用 detect_frame
    print("YOLO 检测模式")
    
    # 调用 YOLO 检测（只调用一次！）
    result, annotated_frame = sys.detector.detect_frame()

    # 检查是否检测到目标
    #这里使用与操作符，是再次检测，确保当前模式是yolo detection\nno image，防止切换为菜单模式，蜂鸣器依旧鸣叫
    if sys.detector.get_if_target_detected() and sys.get_program_mode() != "program menu":
        
        # 调用工具函数，更新舵机跟踪角度
        obj_target_center_x, obj_target_center_y = sys.detector.get_target_center()
        pid_control_servos(sys,obj_target_center_x,obj_target_center_y)
        

        #activate indicator led and buzzer
        sys.rgb_led.set_color_name("red")
        
        if activate_buzzer:
            sys.buzzer.start_alarm()
        
        
        current_d = sys.laser_sensor.distance
        print(f"激光测距距离: {current_d} mm")
        obj_target_center_x, obj_target_center_y = sys.detector.get_target_center()
        print(f"目标的中心坐标是({obj_target_center_x:.2f}, {obj_target_center_y:.2f})")
    else:
        print("未检测到目标")
        # 停止蜂鸣器报警
        sys.buzzer.stop_alarm()
        sys.rgb_led.set_color_name("green")
    

    
    if annotated_frame is not None and result is not None and activate_screen_show:
        cv_show(annotated_frame, result, sys)



def program_mode_feedforward_draw_record_chart(sys):
    # 1. ========== 初始化记录文件路径 (CSV) ==========
    if not hasattr(sys, '_record_file_path') or sys._record_file_path is None:
        current_script_dir = os.path.dirname(os.path.abspath(__file__))
        record_dir = os.path.join(
            current_script_dir, 
            "detection_records_analyse", 
            "detection_records"
        )
        
        if not os.path.exists(record_dir):
            os.makedirs(record_dir)
            
        # 生成带日期和时间的文件名
        file_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data_record_{file_timestamp}.csv"
        sys._record_file_path = os.path.join(record_dir, filename)
        
        # 写入表头，增加 'timestamp' 列
        with open(sys._record_file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'target_x', 'target_y', 'error_x', 'error_y', 'pid_out_x', 'pid_out_y'])

    # 2. ========== 执行 YOLO 检测与控制 ==========
    program_mode_feedforward_control_test(sys, activate_buzzer=False, activate_screen_show=False)

    # 3. ========== 获取数据并写入 ==========
    try:
        # --- 获取当前行的时间戳 (时:分:秒.毫秒) ---
        now_time = datetime.now().strftime("%H:%M:%S.%f")[:-3] 

        # 获取原始数值
        target_center = sys.detector.get_target_center()
        t_x, t_y = target_center if target_center else (0.0, 0.0)
        
        p_out_x, p_out_y = sys.pid_controller.get_PID_controller_output()
        
        err_x = sys.pid_controller.error_x if hasattr(sys.pid_controller, 'error_x') else 0.0
        err_y = sys.pid_controller.error_y if hasattr(sys.pid_controller, 'error_y') else 0.0

        # 格式化数值精度
        values = [t_x, t_y, err_x, err_y, p_out_x, p_out_y]
        formatted_values = [f"{val:.3f}" for val in values]

        # 组合最终写入行：[时间, x, y, err_x, err_y, out_x, out_y]
        final_row = [now_time] + formatted_values

        with open(sys._record_file_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(final_row)
            
    except Exception as e:
        print(f"写入记录失败: {e}")
        
        
def running_code(sys):
    """
    主运行函数：处理视频流、YOLO检测、舵机控制
    :param sys: 系统管理器实例
    """ 
    # sys.program_mode_manager_oled_show()
    current_program_mode = sys.get_program_mode()  # 把当前程序运行模式赋值给current_program_mode 
    
    if current_program_mode == "yolo detection\nno image":
        program_mode_yolo_detection(sys)
    elif current_program_mode == "yolo detection\nvc show":
        program_mode_yolodetection_show(sys)
    elif current_program_mode == "yolo detection\nno buzzer":
        program_mode_yolodetection_show_no_buzzer(sys)
    elif current_program_mode =="yolo detection\nno image no buzzer":
        program_mode_yolodetection_no_show_no_buzzer(sys)
    elif current_program_mode =="draw_record_chart":
        program_mode_draw_record_chart(sys)
    elif current_program_mode == "feedforward_control\ntest":
        program_mode_feedforward_control_test(sys)
    elif current_program_mode == "draw_record_chart\nfeedback_control":
        program_mode_feedforward_draw_record_chart(sys)
    elif current_program_mode == "Kalman_test":
        program_mode_kalman_test(sys)



        
    
        

if __name__ == "__main__":
    # 1. 初始化系统管理器
    with SystemManager() as sys:
        # ✅ 删除了循环前的 detect_frame() 调用
        # 这样可以避免改变初始状态标志位
        sys.program_mode_manager_oled_show()
        
        # 性能监控变量
        frame_count = 0
        start_time = time.time()
        last_print_time = start_time
        
        while True:
            running_code(sys)
            
            # 性能监控
            frame_count += 1
            current_time = time.time()
            
            # 每5秒打印一次帧率
            if current_time - last_print_time >= 5.0:
                elapsed = current_time - start_time
                fps = frame_count / elapsed
                print(f"[PERFORMANCE] Frames: {frame_count}, Time: {elapsed:.2f}s, FPS: {fps:.2f}")
                last_print_time = current_time
