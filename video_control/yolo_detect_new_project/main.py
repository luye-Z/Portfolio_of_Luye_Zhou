import cv2
from yolo_predict import YOLODetector

if __name__ == "__main__":
    #模型路径
    MODEL_PATH = "/home/pi/projects/yolo26/model_folder/ncnn_format_model/640_imgsz_ncnn_model/0207_quadcopter_yolo26_ncnn_model"
    detector = YOLODetector(MODEL_PATH)  #创建YOLODetector对象实例
    detector.start()  #启动树莓派相机
    
    try:
        while True:
            # 调用YOLODetector的detect_frame方法，检测一帧图像
            result, annotated_frame = detector.detect_frame(draw_annotations=True)
            
            # 显示标注后的画面
            cv2.imshow("YOLO Detection (Lightweight)", cv2.resize(annotated_frame, (detector.SCREEN_WIDTH, detector.SCREEN_HEIGHT)))
            
            if cv2.waitKey(1) == ord('q'):
                break
    finally:
        detector.stop()