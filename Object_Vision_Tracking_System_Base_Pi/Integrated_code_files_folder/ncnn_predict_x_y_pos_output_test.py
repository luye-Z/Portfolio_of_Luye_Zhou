import cv2
from picamera2 import Picamera2
from ultralytics import YOLO

# --- 0. 定义分辨率常量 ---
FRAME_WIDTH = 1640
FRAME_HEIGHT = 1232

# 1. Hardware Configuration
picam2 = Picamera2()
config = picam2.create_preview_configuration(main={
    "size": (FRAME_WIDTH, FRAME_HEIGHT), 
    "format": "RGB888"
})
picam2.configure(config)
picam2.start()

# Load NCNN Model
model = YOLO("yolo26n_01_24_quadcopter_best_ncnn_model", task='detect')

print("Streaming started... Press 'q' to quit.")

try:
    while True:
        # Capture frame
        frame = picam2.capture_array()
        
        # Inference
        results = model(frame, imgsz=320, conf=0.25, verbose=False)
        
        annotated_frame = frame.copy() 

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
                if width >= (FRAME_WIDTH * 0.9) or height >= (FRAME_HEIGHT * 0.9):
                    continue

                # --- 核心修改：改为计算中心坐标 ---
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2  # 修改处：现在计算的是垂直方向的中心点
                
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

        # Display
        cv2.imshow("YOLO NCNN Detection", cv2.resize(annotated_frame, (820, 616)))

        if cv2.waitKey(1) == ord("q"):
            break

finally:
    picam2.stop()
    cv2.destroyAllWindows()