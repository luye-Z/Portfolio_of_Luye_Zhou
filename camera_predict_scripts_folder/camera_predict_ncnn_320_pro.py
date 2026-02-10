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
# Using task='detect' to avoid auto-guessing warnings
# model = YOLO("yolo26n_01_24_quadcopter_best_ncnn_model", task='detect')
model = YOLO("/home/pi/projects/yolo26/model_folder/ncnn_format_model/320_imgsz_ncnn_model/0207_quadcopter_yolo26_ncnn_model", task='detect')
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
        results = model(frame, imgsz=320, conf=0.25, verbose=True)
        
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
