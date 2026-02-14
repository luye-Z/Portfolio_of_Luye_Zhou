import cv2
import time
import numpy as np
from picamera2 import Picamera2
from ultralytics import YOLO

class YOLODetector:
    def __init__(self, model_path, imgsz=640, conf=0.25):
        """初始化相机和 YOLO 模型"""
        self.imgsz = imgsz
        self.conf = conf
        
        # 1. 初始化 PiCamera2
        self.picam2 = Picamera2()
        config = self.picam2.create_preview_configuration(
            main={"size": (1640, 1232), "format": "RGB888"}
        )
        self.picam2.configure(config)
        
        # 2. 加载模型
        print(f"[YOLO] Loading model: {model_path}")
        self.model = YOLO(model_path, task='detect')
        
        # 3. 简化性能指标 - 只记录推理时间
        self.frame_counts = 0
        self.total_inference_time = 0  # 只记录推理时间
        self.session_start_time = None

    def start(self):
        """启动相机"""
        self.picam2.start()
        self.session_start_time = time.time()
        print("[YOLO] Camera and Detector started.")

    def stop(self):
        """释放资源并打印报告"""
        duration = time.time() - self.session_start_time
        self._print_report(duration)
        self.picam2.stop()
        cv2.destroyAllWindows()

    def detect_frame(self, draw_annotations=True):
        """抓取一帧并进行识别，返回结果和标注后的帧
        
        参数:
            draw_annotations: 是否绘制检测框和标签（默认True）
            
        返回:
            result: YOLO检测结果
            annotated_frame: 标注后的图像帧
        """
        frame = self.picam2.capture_array()
        
        # 推理
        results = self.model(frame, imgsz=self.imgsz, conf=self.conf, verbose=False)
        result = results[0]

        # 记录性能数据 - 只记录推理时间
        self.frame_counts += 1
        self.total_inference_time += result.speed['inference']
        
        # 根据参数决定是否绘制标注
        if draw_annotations:
            annotated_frame = self.draw_annotations(frame, result)
        else:
            annotated_frame = frame.copy()
            
        return result, annotated_frame
    
    def draw_annotations(self, frame, result):
        """使用OpenCV轻量级绘制检测框和标签
        
        参数:
            frame: 原始图像帧
            result: YOLO检测结果
            
        返回:
            annotated_frame: 绘制了检测框的图像
        """
        # 复制原始帧，避免修改原图
        annotated_frame = frame.copy()
        
        # 获取检测结果
        boxes = result.boxes
        
        if boxes is not None and len(boxes) > 0:
            # 遍历所有检测框
            for box in boxes:
                # 获取边界框坐标
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                confidence = box.conf[0].item()
                
                # 过滤低置信度检测（虽然模型已经过滤，但这里再次确认）
                if confidence < self.conf:
                    continue
                
                # 绘制检测框（绿色）
                cv2.rectangle(annotated_frame, 
                              (int(x1), int(y1)), 
                              (int(x2), int(y2)), 
                              (0, 255, 0), 2)
                
                # 绘制置信度标签（黄色）
                label = f"{confidence*100:.1f}%"
                label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                
                # 绘制标签背景
                cv2.rectangle(annotated_frame,
                              (int(x1), int(y1) - label_size[1] - 10),
                              (int(x1) + label_size[0], int(y1)),
                              (0, 255, 255), -1)
                
                # 绘制标签文字
                cv2.putText(annotated_frame, label,
                           (int(x1), int(y1) - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        
        return annotated_frame

    def _print_report(self, duration):
        """内部方法：打印简化性能报告"""
        if self.frame_counts > 0:
            avg_inference = self.total_inference_time / self.frame_counts
            avg_fps = self.frame_counts / duration
            print("\n" + "="*40)
            print(f"🚀 YOLO PERFORMANCE REPORT")
            print(f"Frames Processed: {self.frame_counts}")
            print(f"Session Duration: {duration:.2f}s")
            print(f"Average FPS: {avg_fps:.2f}")
            print(f"Average Inference Time: {avg_inference:.2f}ms")
            print("="*40)

# --- 单元测试 ---
if __name__ == "__main__":
    MODEL_PATH = "/home/pi/projects/yolo26/model_folder/ncnn_format_model/640_imgsz_ncnn_model/0207_quadcopter_yolo26_ncnn_model"
    detector = YOLODetector(MODEL_PATH)
    detector.start()
    
    try:
        while True:
            result, annotated_frame = detector.detect_frame(draw_annotations=True)
            
            # 显示标注后的画面
            cv2.imshow("YOLO Detection (Lightweight)", cv2.resize(annotated_frame, (820, 616)))
            
            if cv2.waitKey(1) == ord('q'):
                break
    finally:
        detector.stop()