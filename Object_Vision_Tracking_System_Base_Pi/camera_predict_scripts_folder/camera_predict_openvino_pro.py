import cv2
import time
from picamera2 import Picamera2
from ultralytics import YOLO

# 1. Hardware Configuration (树莓派摄像头配置)
picam2 = Picamera2() #Picamera2 是模块里面定义的一个类，picam2 是我们自己定义的一个实例
#IMX219 camera
config = picam2.create_preview_configuration(main={
    # "size": (int(1640*0.52), int(1232*0.52)),  #深度优化代码，提升模型运行速度
    "size": (864, 640),
    # "size": (640, 448), #原始分辨率，保持全视野（FOV）
    "format": "RGB888"
})# 创建config配置：    

picam2.configure(config) # 将上面定义好的分辨率和格式正式“刷”入硬件寄存器
picam2.start() # 启动摄像头：

# ---加载 OpenVINO 模型 ---
# 指向 export 后生成的包含 .xml 和 .bin 的文件夹路径
#指向存放模型的文件夹
model_path = "/home/pi/projects/yolo26/model_folder/OpenVINO/640_imgsz_model/0207_quadcopter_yolo26_openvino_model"
model = YOLO(model_path, task='detect') # 加载并实例化模型：

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
        frame = picam2.capture_array()#将摄像头捕捉到的光学信号直接转换为内存中的 NumPy 矩阵（数据信息），
        
        # 正式启动YOLO 推理
        results = model(frame, imgsz=640, conf=0.25, verbose=False, device='cpu')
        #函数 "model" 参数介绍 , frame 是输入的图像帧（NumPy 数组）,上面定义过了，
        # imgsz=640 是模型的输入图像大小，必须与导出时的大小一致（640）
        # conf=0.25 是置信度阈值，模型会给置信度大于25%的目标大框保留下来
        # verbose=False 表示不打印详细的推理信息，只返回结果，静默模式
        # device='cpu'，指定计算机硬件
        
        # Accumulate timing
        speed = results[0].speed   #results[0].speed 返回的是一个包含三个关键阶段耗时的 Python 字典。
        total_preprocess_time += speed['preprocess']  # preprocess 预处理耗时（把图片缩放到 640x640 的时间）
        total_inference_time += speed['inference']    # inference 推理耗时（神经网络在 CPU 上跑数学计算的时间）
        total_postprocess_time += speed['postprocess'] # postprocess后处理耗时（整理坐标、滤掉置信度低的框的时间）
        frame_counts += 1

        # Plotting
        annotated_frame = results[0].plot()  #将YOLO检测结果赋值给annotated_frame，用于后续显示

        # Calculate Real-time FPS 
        latency_ms = sum(speed.values())  #keys() and valeues() 组成了dictionary 
        rt_fps = 1000 / latency_ms if latency_ms > 0 else 0  #  python 如果 if 语句为真，执行前面的语句
        
        cv2.putText(annotated_frame, f"OpenVINO FPS: {rt_fps:.1f}", (30, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)

        # Display (调整显示尺寸以降低 UI 压力)
        # cv2.imshow("YOLO OpenVINO Detection", cv2.resize(annotated_frame, (864, 640)))
        #如果不调整尺寸
        cv2.imshow("YOLO OpenVINO Detection", annotated_frame)
        
        #======================================
        # 在 cv2.imshow 之后
        # 1. 强制切断结果对象对原始图片的“占有”
        results[0].orig_img = None 
        
        # 2. 将大变量直接赋值为 None（这比 del 更能直接触发 Python 的回收机制）
        results = None
        annotated_frame = None
        frame = None
        #====================================
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
