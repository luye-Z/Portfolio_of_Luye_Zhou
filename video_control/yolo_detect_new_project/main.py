import cv2
# from yolo_predict import YOLODetector
# from buzzer_driver import BuzzerController
# from vl53l0x_drive_threat import VL53L0X_Threaded

from system_manager import SystemManager

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
        # 没有检测到目标，直接返回
        cv2.imshow("YOLO Detection", annotated_frame)
        return False

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

    # 3. 直接显示（不缩放，保持最高清晰度）
    cv2.imshow("YOLO Detection", annotated_frame)

    # 4. 退出逻辑
    if cv2.waitKey(1) == ord("q"):
        return True
    return False

if __name__ == "__main__":

    with SystemManager() as sys:
        
       
        while True:
            # 调用YOLODetector的detect_frame方法，检测一帧图像
            result, annotated_frame = sys.detector.detect_frame()
            
            #调用CV显示逻辑
            cv_show(annotated_frame, result,sys)
            
            
            if sys.detector.get_target_detected():
                
                #调用舵机控制器跟踪目标
                sys.servo_controller.track_target( sys.detector.get_target_center_x(), sys.detector.get_target_center_y(), sys.detector.SCREEN_WIDTH, sys.detector.SCREEN_HEIGHT)
                
                print("目标检测到")
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
                sys.rgb_led.off()
                
            # 显示标注后的画面
            # cv2.imshow("YOLO Detection (Lightweight)", cv2.resize(annotated_frame, (detector.SCREEN_WIDTH, detector.SCREEN_HEIGHT)))
            
            # if cv2.waitKey(1) == ord('q'):
            #     break
     