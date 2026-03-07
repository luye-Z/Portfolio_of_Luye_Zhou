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
    极简显示函数：只画框和原始视频
    :param frame: 原始图像帧
    :param results: YOLO 推理结果
    :return: 是否按下退出键 (True/False)
    """
    # 直接在原始帧的副本上绘制，保持分辨率一致
    annotated_frame = frame.copy()
    
    # 1. 确保结果不为空
    if len(results) == 0 or len(results[0].boxes) == 0:
        # 没有检测到目标，显示原图
        cv2.imshow("YOLO Detection", annotated_frame)
    else:
        # 2. 绘制检测框
        for box in results[0].boxes:
            # 获取坐标
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            conf = box.conf[0].item()
            cls = int(box.cls[0].item())
            
            # 之前的过滤逻辑：如果框太大（超过屏幕55%），通常是误检或离得太近，跳过不画
            w, h = x2 - x1, y2 - y1
            if w >= (sys.detector.SCREEN_WIDTH * 0.55) or h >= (sys.detector.SCREEN_HEIGHT * 0.55):
                continue
            
            # 画矩形框 (绿色，线条宽度为2)
            cv2.rectangle(annotated_frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
            
            # 简易标签 (类别ID + 置信度)
            label = f"ID:{cls} {conf:.2f}"
            cv2.putText(annotated_frame, label, (int(x1), int(y1) - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # 显示带框图像
        cv2.imshow("YOLO Detection", annotated_frame)
    
    # 3. 退出逻辑：按 'q' 键退出
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        return True
    
    return False


def program_mode_yolodetection_no_show(sys , activate_buzzer=True): #添加了蜂鸣器控制参数，默认开启蜂鸣器
    """
    YOLO检测模式（不显示图像,不使用智能控制）
    修复版本：正确的模式切换逻辑
    """
    annotated_frame = None
    result = None
            

    # YOLO 检测模式：调用 detect_frame
    print("YOLO 检测模式")
    
    # 调用 YOLO 检测（只调用一次！）
    result, annotated_frame = sys.detector.detect_frame()

    # 检查是否检测到目标
    #这里使用与操作符，是再次检测，确保当前模式是yolo detection\nno image，防止切换为菜单模式，蜂鸣器依旧鸣叫
    if sys.detector.get_if_target_detected() and sys.get_program_mode() == "yolo detection\nno image":
        

        # 调用舵机控制器跟踪目标
        obj_target_center_x, obj_target_center_y = sys.detector.get_target_center()
        # 调用 PID 控制器计算角度
        sys.pid_controller.pid_control_calculate(
            obj_target_center_x, 
            obj_target_center_y, 
            sys.detector.SCREEN_WIDTH, 
            sys.detector.SCREEN_HEIGHT
        )
         # 获取 PID 控制器输出
        pan_controller_output, tilt_controller_output = sys.pid_controller.get_PID_controller_output()
        #控制舵机运动
        sys.servo_controller.set_pan_angle(pan_controller_output)
        sys.servo_controller.set_tilt_angle(tilt_controller_output)
        

        #activate indicator led and buzzer
        sys.rgb_led.set_color_name("red")
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
    

    
    return annotated_frame, result



def program_mode_yolodetection_show(sys):
    """
    YOLO检测模式（显示图像）
    """
    annotated_frame, result = program_mode_yolodetection_no_show(sys)
    
    # 添加空值检查，防止None被传入cv_show
    if annotated_frame is not None and result is not None:
        quit_flag = cv_show(annotated_frame, result, sys)
        return quit_flag
    
    return False

def program_mode_yolodetection_no_show_no_buzzer(sys):

    program_mode_yolodetection_no_show(sys , activate_buzzer=False)
    
    
def program_mode_yolodetection_show_no_buzzer(sys):   
    annotated_frame, result = program_mode_yolodetection_no_show_no_buzzer(sys)
    
    # 添加空值检查，防止None被传入cv_show
    if annotated_frame is not None and result is not None:
        quit_flag = cv_show(annotated_frame, result, sys)
        return quit_flag
    
    return False



def program_mode_draw_record_chart(sys):
    """
    绘制记录图表模式
    基于 YOLO 检测模式，把每一次检测到的目标中心点坐标记录到文件中。
    在当前路径下新建 detection_records 文件夹，按时间戳新建 CSV 文件。
    """
    
def program_mode_draw_record_chart(sys):
    annotated_frame = None
    result = None

    # 1. ========== 初始化记录文件 (CSV) ==========
    if not hasattr(sys, '_record_file_path') or sys._record_file_path is None:
        # --- 核心修改：相对路径定位 ---
        # 获取当前脚本 (main_test.py) 所在的绝对目录
        current_script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 定位到 detection_records_analyse/detection_records
        record_dir = os.path.join(
            current_script_dir, 
            "detection_records_analyse", 
            "detection_records"
        )
        
        # 确保目录存在
        os.makedirs(record_dir, exist_ok=True)
        
        # 记录本次运行的时间戳
        sys._run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sys._record_file_path = os.path.join(record_dir, f"record_{sys._run_timestamp}.csv")
        
        # 创建文件并写入表头
        with open(sys._record_file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "center_x", "center_y"])
        print(f"[SYSTEM] 相对路径记录已启动: {sys._record_file_path}")

    # 2. ========== YOLO 检测逻辑 ==========
    if sys.detector.get_yolo_detect_turn():
        result, annotated_frame = sys.detector.detect_frame()
        sys.detector.update_smart_control_params()
        sys.detector.reverse_yolo_detect_turn()

        if sys.detector.get_if_target_detected():
            sys.rgb_led.set_color_name("red")
            x, y = sys.detector.get_target_center()

            # 写入 CSV
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            with open(sys._record_file_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([current_time, f"{x:.2f}", f"{y:.2f}"])

            # 舵机跟踪
            sys.pid_controller.pid_control_calculate(x, y, sys.detector.SCREEN_WIDTH, sys.detector.SCREEN_HEIGHT)
            
            # --- 核心：每帧更新后重新绘制并保存图片 ---
            # 为了性能，建议你可以根据需要设置触发频率，比如每 10 帧更新一次图表
            # 或者在程序结束时调用。这里演示实时保存：
        else:
            sys.rgb_led.set_color_name("green")

    else:
        # 智能控制模式
        sys.detector.reverse_yolo_detect_turn()
        if sys.detector.get_if_target_detected():
            p_x, p_y = sys.detector.calculate_smart_control_target_center()
            sys.pid_controller.pid_control_calculate(p_x, p_y, sys.detector.SCREEN_WIDTH, sys.detector.SCREEN_HEIGHT)

    return annotated_frame, result
    
     
def running_code(sys):
    """
    主运行函数：处理视频流、YOLO检测、舵机控制
    :param sys: 系统管理器实例
    """ 
    # sys.program_mode_manager_oled_show()
    current_program_mode = sys.get_program_mode()  # 把当前程序运行模式赋值给current_program_mode 
    
    if current_program_mode == "yolo detection\nno image":
        program_mode_yolodetection_no_show(sys)
    elif current_program_mode == "yolo detection\nvc show":
        program_mode_yolodetection_show(sys)
    elif current_program_mode == "yolo detection\nno buzzer":
        program_mode_yolodetection_show_no_buzzer(sys)
    elif current_program_mode =="yolo detection\nno image no buzzer":
        program_mode_yolodetection_no_show_no_buzzer(sys)
    elif current_program_mode =="draw_record_chart":
        program_mode_draw_record_chart(sys)

        
    
        

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