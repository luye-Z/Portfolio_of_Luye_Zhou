import cv2
from yolo_predict import YOLODetector
from system_manager import SystemManager

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


def running_code(sys):
    """
    主运行函数：处理视频流、YOLO检测、舵机控制
    :param sys: 系统管理器实例
    """ 
    current_program_mode = sys.get_program_mode() #把当前程序运行模式赋值给current_program_mode    
    

if __name__ == "__main__":
    # 1. 初始化系统管理器，和start方法
    with SystemManager() as sys:
        # 2. 只在循环外调用一次 detect_frame，避免重复调用
        result, annotated_frame = sys.detector.detect_frame()
        

        
        while True:
            # 3. 检查是否需要切换到智能控制模式
            
            # #测试代码
            # print(sys.detector.get_yolo_detect_turn())
            # print(sys.detector.get_yolo_detect_turn())
            # print(sys.detector.get_yolo_detect_turn())
            
            
            if not sys.detector.get_yolo_detect_turn():
                
                # 智能控制模式：不调用 detect_frame，直接使用预估坐标
                print("智能控制模式")
                sys.detector.reverse_yolo_detect_turn()
                
                if sys.detector.get_target_detected():
                    # 获取预估坐标
                    smart_predicted_target_center_xy_tuple = sys.detector.calculate_smart_control_target_center()
                    
                    # 调用舵机控制器跟踪目标
                    sys.servo_controller.track_target(
                        smart_predicted_target_center_xy_tuple[0], 
                        smart_predicted_target_center_xy_tuple[1], 
                        sys.detector.SCREEN_WIDTH, 
                        sys.detector.SCREEN_HEIGHT
                    )
                    
                    # 更新智能控制参数
                
            else:
                
                print("YOLO 检测模式")
                #更新数据，并且翻转YOLO检测模式

                # YOLO 检测模式：调用 detect_frame
                
                
                # 调用 YOLO 检测（只调用一次！）
                result, annotated_frame = sys.detector.detect_frame()
                
                # 更新智能控制参数
                sys.detector.update_smart_control_params()
                #翻转模式选择标志位
                sys.detector.reverse_yolo_detect_turn()
                
                # 更新智能控制参数
                # print(f"Pitch: {sys.mpu6050.get_mpu6050_angle_pose()[0]:.2f}°, Roll: {sys.mpu6050.get_mpu6050_angle_pose()[1]:.2f}°")
            # 4. 检查是否检测到目标
                if sys.detector.get_target_detected():
                    # sys.oled.show_text(f"objection detected !", size=12)
                    sys.rgb_led.set_color_name("red")
                    
                    # 调用舵机控制器跟踪目标
                    obj_target_center_x, obj_target_center_y = sys.detector.get_target_center()
                    sys.servo_controller.track_target(
                        obj_target_center_x, 
                        obj_target_center_y, 
                        sys.detector.SCREEN_WIDTH, 
                        sys.detector.SCREEN_HEIGHT
                    )
                    
                    # 启动蜂鸣器报警
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
                    # sys.oled.clear()
                
            #5. 调用 CV 屏幕显示逻辑
            quit_flag = cv_show(annotated_frame, result, sys)
            
            # 6. 如果返回 True（按下了 Q），则跳出循环
            if quit_flag:
                print("检测到退出信号，正在关闭系统...")
                break
