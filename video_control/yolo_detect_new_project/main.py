import cv2
from yolo_predict import YOLODetector
from buzzer_driver import BuzzerController
if __name__ == "__main__":
    #模型路径
    MODEL_PATH = "/home/pi/projects/yolo26/model_folder/ncnn_format_model/640_imgsz_ncnn_model/0207_quadcopter_yolo26_ncnn_model"
    
    detector = YOLODetector(MODEL_PATH)  #创建YOLODetector对象实例
    detector.start()  #启动树莓派相机
    
    # 创建蜂鸣器控制器实例
    buzzer = BuzzerController()
    
    try:
        while True:
            # 调用YOLODetector的detect_frame方法，检测一帧图像
            result, annotated_frame = detector.detect_frame(draw_annotations=True)
            if detector.get_target_detected():
                
                print("目标检测到")
                # 启动蜂鸣器报警
                buzzer.start_alarm()
                
                obj_target_center_x, obj_target_center_y = detector.get_target_center()
                print(f"目标的中心坐标是({obj_target_center_x:.2f}, {obj_target_center_y:.2f})")
            else:
                print("未检测到目标")
                # 停止蜂鸣器报警
                buzzer.stop_alarm()
                
            # 显示标注后的画面
            cv2.imshow("YOLO Detection (Lightweight)", cv2.resize(annotated_frame, (detector.SCREEN_WIDTH, detector.SCREEN_HEIGHT)))
            
            if cv2.waitKey(1) == ord('q'):
                break
    finally:
        detector.stop()
        buzzer.cleanup()