import cv2
import time
from picamera2 import Picamera2
from ultralytics import YOLO

# 1. 硬件级优化：使用中等分辨率以保持全视野 (FOV)
# 1640x1232 是 3280x2460 的完美 2x2 像素融合（Binning）
picam2 = Picamera2()
config = picam2.create_preview_configuration(main={
    "size": (1640, 1232), 
    "format": "RGB888"
})
picam2.configure(config)
picam2.start()

# 加载模型
#model = YOLO("yolo11n.pt")
model = YOLO("/home/pi/projects/yolo26/model_folder/yolo26n.pt")
# model = YOLO("yolo26n_ncnn_model")
prev_time = time.time()

while True:
    # 此时 frame 的尺寸只有原来的 1/4，CPU 负担大幅降低
    frame = picam2.capture_array()

    # 2. 推理优化：imgsz=320 至少能让速度提升 1 倍以上
    # verbose=False 可以减少终端日志打印带来的微小延迟
    results = model(frame, imgsz=640, conf=0.25, verbose=True)

    # 3. 绘图优化：直接在 1640x1232 的图上绘图
    annotated_frame = results[0].plot()

    # 计算 FPS
    curr_time = time.time()
    fps = 1 / (curr_time - prev_time)
    prev_time = curr_time

    # 显示 FPS
    cv2.putText(annotated_frame, f"FPS: {fps:.1f}", (30, 60), 
                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)

    # 4. 显示：此时无需再做 cv2.resize，直接显示 1640 分辨率
    # 如果窗口太大，可以改为 cv2.imshow("Camera", cv2.resize(annotated_frame, (820, 616)))
    cv2.imshow("Camera", annotated_frame)

    if cv2.waitKey(1) == ord("q"):
        break

picam2.stop()
cv2.destroyAllWindows()
