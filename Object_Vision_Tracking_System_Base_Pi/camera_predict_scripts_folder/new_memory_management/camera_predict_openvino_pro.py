import cv2
import time
import gc
import tracemalloc  # 新增：内存追踪
import numpy as np
from picamera2 import Picamera2
from ultralytics import YOLO

# 1. 启用内存追踪
tracemalloc.start()

# 2. 强制设置OpenCV不使用内存池
cv2.setNumThreads(0)  # 禁用多线程，减少内存碎片
cv2.ocl.setUseOpenCL(False)  # 禁用OpenCL，避免GPU内存泄漏

# 3. 硬件配置
picam2 = Picamera2()
config = picam2.create_preview_configuration(
    main={
        "size": (864, 640),
        "format": "RGB888"
    },
    buffer_count=2  # 关键：减少缓冲区数量
)
picam2.configure(config)
picam2.start()

# 4. 加载模型 - 使用单例模式
print("Loading model...")
model_path = "/home/pi/projects/yolo26/model_folder/OpenVINO/640_imgsz_model/0207_quadcopter_yolo26_openvino_model"
model = YOLO(model_path, task='detect')

# 5. 全局计数器
frame_count = 0
start_time = time.time()
last_gc_time = time.time()
gc_interval = 5  # 每5秒强制GC一次
frame_skip = 1  # 处理帧间隔，设为1表示处理每一帧

# 6. 内存监控函数
def check_memory():
    current, peak = tracemalloc.get_traced_memory()
    return current / 10**6, peak / 10**6  # 返回MB

print(f"Initial memory: {check_memory()[0]:.2f} MB")
print("Inference started... Press 'q' to quit.")

# 7. 创建显示窗口（仅一次）
cv2.namedWindow("YOLO OpenVINO Detection", cv2.WINDOW_NORMAL)

try:
    while True:
        current_time = time.time()
        
        # 8. 定期内存清理
        if current_time - last_gc_time > gc_interval:
            # 强制所有清理
            gc.collect(generation=2)  # 完全GC
            gc.collect(generation=1)
            gc.collect(generation=0)
            
            current_mem, peak_mem = check_memory()
            print(f"[Memory] Current: {current_mem:.2f} MB, Peak: {peak_mem:.2f} MB")
            last_gc_time = current_time
            
            # 每100帧重置追踪器
            if frame_count % 100 == 0:
                tracemalloc.reset_peak()
        
        # 9. 采集帧 - 使用固定内存块
        try:
            # 创建固定大小的numpy数组（避免重新分配）
            if 'frame_buffer' not in locals():
                frame_buffer = np.zeros((640, 864, 3), dtype=np.uint8)
            
            # 直接写入buffer
            frame_array = picam2.capture_array()
            np.copyto(frame_buffer, frame_array)
            
            # 立即释放原始帧
            del frame_array
        except Exception as e:
            print(f"Frame capture error: {e}")
            time.sleep(0.01)
            continue
        
        # 10. 选择性处理帧（减轻负载）
        frame_count += 1
        if frame_count % frame_skip != 0:
            # 显示原始帧
            cv2.imshow("YOLO OpenVINO Detection", frame_buffer)
            if cv2.waitKey(1) == ord("q"):
                break
            continue
        
        # 11. 推理 - 使用stream=False避免生成器内存泄漏
        try:
            # 【关键修改】使用stream=False，使用单次推理模式
            results = model(frame_buffer, 
                          imgsz=640, 
                          conf=0.25, 
                          verbose=False, 
                          device='cpu',
                          stream=False,  # 关键：不使用stream模式
                          max_det=10)  # 限制检测数量
            
            # 12. 直接在缓冲区上绘制（零拷贝）
            if results and hasattr(results[0], 'boxes') and results[0].boxes is not None:
                boxes = results[0].boxes
                if boxes.xyxy.numel() > 0:
                    boxes_np = boxes.xyxy.cpu().numpy()
                    confs_np = boxes.conf.cpu().numpy()
                    classes_np = boxes.cls.cpu().numpy()
                    
                    for i in range(len(boxes_np)):
                        x1, y1, x2, y2 = map(int, boxes_np[i])
                        conf = confs_np[i]
                        cls = int(classes_np[i])
                        label = f"{model.names[cls]} {conf:.2f}"
                        
                        # 画框
                        cv2.rectangle(frame_buffer, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        # 画标签
                        (text_width, text_height), _ = cv2.getTextSize(
                            label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2
                        )
                        cv2.rectangle(frame_buffer, 
                                     (x1, y1 - text_height - 5),
                                     (x1 + text_width, y1), 
                                     (0, 255, 0), -1)
                        cv2.putText(frame_buffer, label, (x1, y1 - 5),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
            
            # 13. 计算并显示FPS
            latency_ms = sum(results[0].speed.values()) if hasattr(results[0], 'speed') else 0
            rt_fps = 1000 / latency_ms if latency_ms > 0 else 0
            
            # 显示FPS背景框
            cv2.rectangle(frame_buffer, (20, 30), (200, 90), (0, 0, 0), -1)
            cv2.putText(frame_buffer, f"FPS: {rt_fps:.1f}", (30, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
            
            # 显示总帧数
            cv2.putText(frame_buffer, f"Frame: {frame_count}", (30, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
            
        except Exception as e:
            print(f"Inference error: {e}")
        
        # 14. 显示帧
        cv2.imshow("YOLO OpenVINO Detection", frame_buffer)
        
        # 15. 【关键】强制释放推理结果
        if 'results' in locals():
            for r in results:
                if hasattr(r, 'boxes'):
                    r.boxes = None
                if hasattr(r, 'orig_img'):
                    r.orig_img = None
            del results
        
        # 16. 检查退出
        if cv2.waitKey(1) == ord("q"):
            break
            
finally:
    # 17. 最终清理
    print("Cleaning up...")
    
    # 关闭窗口
    cv2.destroyAllWindows()
    
    # 停止摄像头
    picam2.stop()
    
    # 删除所有变量
    if 'frame_buffer' in locals():
        del frame_buffer
    if 'model' in locals():
        del model
    
    # 强制GC
    for _ in range(3):
        gc.collect()
    
    # 停止内存追踪
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    print(f"Final memory: {current_mem:.2f} MB")
    print(f"Peak memory: {peak_mem:.2f} MB")
    tracemalloc.stop()
    
    print("Cleanup completed.")