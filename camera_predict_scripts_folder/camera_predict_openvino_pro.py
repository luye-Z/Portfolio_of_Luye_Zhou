import cv2
import time
from picamera2 import Picamera2
from ultralytics import YOLO

# 1. Hardware Configuration (树莓派摄像头配置)
picam2 = Picamera2()
config = picam2.create_preview_configuration(main={
    "size": (1640, 1232),
    "format": "RGB888"
})
picam2.configure(config)
picam2.start()

# --- 修改部分：加载 OpenVINO 模型 ---
# 指向 export 后生成的包含 .xml 和 .bin 的文件夹路径
model_path = "/home/pi/projects/yolo26/model_folder/OpenVINO/640_imgsz_model/0207_quadcopter_yolo26_openvino_model"
model = YOLO(model_path, task='detect')

# --- Performance Metrics Initialization ---
frame_counts = 0
total_inference_time = 0
total_preprocess_time = 0
total_postprocess_time = 0
session_start_time = time.time()

print("OpenVINO Inference started... Press 'q' to quit.")

try:
    while True:
        # Capture frame
        frame = picam2.capture_array()
        
        # Inference
        # device='cpu' 确保使用 OpenVINO 的 CPU 优化引擎
        results = model(frame, imgsz=640, conf=0.25, verbose=False, device='cpu')
        
        # Accumulate timing
        speed = results[0].speed
        total_preprocess_time += speed['preprocess']
        total_inference_time += speed['inference']
        total_postprocess_time += speed['postprocess']
        frame_counts += 1

        # Plotting
        annotated_frame = results[0].plot()

        # Calculate Real-time FPS
        latency_ms = sum(speed.values())
        rt_fps = 1000 / latency_ms if latency_ms > 0 else 0
        
        cv2.putText(annotated_frame, f"OpenVINO FPS: {rt_fps:.1f}", (30, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)

        # Display (调整显示尺寸以降低 UI 压力)
        cv2.imshow("YOLO OpenVINO Detection", cv2.resize(annotated_frame, (820, 616)))

        if cv2.waitKey(1) == ord("q"):
            break

finally:
    # --- Performance Analysis Log ---
    session_end_time = time.time()
    total_duration = session_end_time - session_start_time
    
    if frame_counts > 0:
        avg_pre = total_preprocess_time / frame_counts
        avg_inf = total_inference_time / frame_counts
        avg_post = total_postprocess_time / frame_counts
        avg_total_latency = avg_pre + avg_inf + avg_post
        avg_fps = frame_counts / total_duration

        print("\n" + "="*40)
        print("🚀 YOLO OPENVINO PERFORMANCE REPORT")
        print("="*40)
        print(f"Total Frames Processed:  {frame_counts}")
        print(f"Avg Inference:          {avg_inf:.2f} ms")
        print(f"AVG PIPELINE FPS:       {avg_fps:.2f}")
        print("-" * 40)
        
    picam2.stop()
    cv2.destroyAllWindows()
