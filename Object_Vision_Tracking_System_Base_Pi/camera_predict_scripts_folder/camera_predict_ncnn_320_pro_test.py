import cv2
import time
from picamera2 import Picamera2
from ultralytics import YOLO

# 1. Hardware Configuration
picam2 = Picamera2()
config = picam2.create_preview_configuration(main={
    "size": (1640, 1232), 
    "format": "RGB888"
})
picam2.configure(config)
picam2.start()

# Load NCNN Model
model = YOLO("yolo26n_01_24_quadcopter_best_ncnn_model", task='detect')

# --- Performance Metrics Initialization ---
frame_counts = 0
total_inference_time = 0
total_preprocess_time = 0
total_postprocess_time = 0
session_start_time = time.time()

print("Streaming started... Press 'q' to quit and view Performance Report.")

try:
    while True:
        # Capture frame
        frame = picam2.capture_array()
        
        # Inference
        # imgsz must match your NCNN export size (320)
        results = model(frame, imgsz=320, conf=0.25, verbose=False)
        
        for result in results:
            boxes = result.boxes  # 所有的检测框
            for box in boxes:
                # 获取坐标 (Tensor格式转为列表)
                x1, y1, x2, y2 = box.xyxy[0].tolist()  # 左上角 (x1, y1) 和 右下角 (x2, y2)
                
                # 计算中心底部坐标
                center_x = (x1 + x2) / 2  # 中心X
                bottom_y = y2  # 底部Y为框的右下角Y坐标
                
                # 打印中心底部坐标
                print(f"检测到物体: 中心底部坐标: ({center_x:.0f}, {bottom_y:.0f})")
        
        # Accumulate timing from Ultralytics internal dictionary (ms)
        speed = results[0].speed
        total_preprocess_time += speed['preprocess']
        total_inference_time += speed['inference']
        total_postprocess_time += speed['postprocess']
        frame_counts += 1

        # Plotting
        annotated_frame = results[0].plot()

        # Calculate Real-time FPS for display
        latency_ms = sum(speed.values())
        rt_fps = 1000 / latency_ms if latency_ms > 0 else 0
        
        cv2.putText(annotated_frame, f"FPS: {rt_fps:.1f}", (30, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)

        # Display (Resized for UI comfort)
        cv2.imshow("YOLO NCNN Detection", cv2.resize(annotated_frame, (820, 616)))

        if cv2.waitKey(1) == ord("q"):
            break

finally:
    # --- Performance Analysis Log (English) ---
    session_end_time = time.time()
    total_duration = session_end_time - session_start_time
    
    if frame_counts > 0:
        avg_pre = total_preprocess_time / frame_counts
        avg_inf = total_inference_time / frame_counts
        avg_post = total_postprocess_time / frame_counts
        avg_total_latency = avg_pre + avg_inf + avg_post
        avg_fps = frame_counts / total_duration

        print("\n" + "="*40)
        print("🚀 YOLO NCNN PERFORMANCE REPORT")
        print("="*40)
        print(f"Total Frames Processed:  {frame_counts}")
        print(f"Total Session Duration: {total_duration:.2f} s")
        print("-" * 40)
        print(f"Avg Preprocess:         {avg_pre:.22f} ms")
        print(f"Avg Inference:          {avg_inf:.22f} ms")
        print(f"Avg Postprocess:        {avg_post:.22f} ms")
        print(f"Avg Total Latency:      {avg_total_latency:.22f} ms")
        print("-" * 40)
        print(f"AVG PIPELINE FPS:       {avg_fps:.2f}")
        
        # Bottleneck Analysis
        if avg_inf > (avg_pre + avg_post):
            bottleneck = "Neural Network Inference (CPU bound)"
        else:
            bottleneck = "Image I/O or Rendering"
        print(f"Primary Bottleneck:     {bottleneck}")
        print("="*40)

    picam2.stop()
    cv2.destroyAllWindows()
