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
        
        self.SCREEN_WIDTH = 864
        self.SCREEN_HEIGHT = 640
        # 1. 初始化 PiCamera2
        self.picam2 = Picamera2()
        config = self.picam2.create_preview_configuration(
            main={"size": (self.SCREEN_WIDTH, self.SCREEN_HEIGHT), "format": "RGB888"}
        )
        self.picam2.configure(config)
        
        # 2. 加载模型
        print(f"[YOLO] Loading model: {model_path}")
        self.model = YOLO(model_path, task='detect')
        
        # 3. 简化性能指标 - 只记录推理时间
        self.frame_counts = 0
        self.total_inference_time = 0  # 只记录推理时间
        self.session_start_time = None
        
        #4.数据成员，是否检测到目标，布尔变量，标志位
        self.target_detected = False 
        #5. 目标中心坐标
        
        self.target_center_x = self.SCREEN_WIDTH/2
        self.target_center_y = self.SCREEN_HEIGHT/2
        
        
        
        # 标志位，用于计数，是否调用YOLO—detect_frame方法,只有两种状态，另一种状态直接调用预估像素坐标数据进行控制
        self.yolo_detect_turn = True   
        
        #SMART CONTROL 参数预先存储
        self.smart_last_target_center_x = self.SCREEN_WIDTH/2
        self.smart_last_target_center_y = self.SCREEN_HEIGHT/2
        self.smart_now_target_center_x = self.SCREEN_WIDTH/2
        self.smart_now_target_center_y = self.SCREEN_HEIGHT/2
    
    def update_smart_control_params(self):
        
        """更新SMART CONTROL 参数"""
        """这个参数更新只在 实际执行yolo_detect 轮次执行"""
        self.smart_last_target_center_x = self.smart_now_target_center_x
        self.smart_last_target_center_y = self.smart_now_target_center_y
        self.smart_now_target_center_x = self.get_target_center_x()
        self.smart_now_target_center_y = self.get_target_center_y()
        # 切换标志位,
        self.yolo_detect_turn = not self.yolo_detect_turn
    
    def get_smart_control_params(self):
        """获取SMART CONTROL 参数"""
        return self.smart_last_target_center_x, self.smart_last_target_center_y, self.smart_now_target_center_x, self.smart_now_target_center_y
    
    def calculate_smart_control_target_center(self):
        """计算智能超前预估控制的目标中心坐标"""
        
        dx = self.smart_now_target_center_x - self.smart_last_target_center_x
        dy = self.smart_now_target_center_y - self.smart_last_target_center_y
        smart_predicted_target_center_x = self.smart_now_target_center_x + dx
        smart_predicted_target_center_y = self.smart_now_target_center_y + dy
        
        return smart_predicted_target_center_x, smart_predicted_target_center_y
        
        
    def get_yolo_detect_turn(self):
        """获取self.yolo_detect_turn的接口方法"""
        return self.yolo_detect_turn
        
        
    def get_target_detected(self):
        """获取是否检测到目标"""
        return self.target_detected
    
    def get_target_center(self):
        """获取目标中心坐标"""
        return self.target_center_x, self.target_center_y
    
    def get_target_center_x(self):
        """获取目标中心坐标"""
        return self.target_center_x
    
    def get_target_center_y(self):
        """获取目标中心坐标"""
        return  self.target_center_y    
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
    
    def cleanup(self):
        """释放所有资源（同 stop）
        
        使用示例：
            detector = YOLODetector(MODEL_PATH)
            detector.start()
            try:
                # 使用检测器...
                pass
            finally:
                detector.cleanup()  # 释放所有资源
        """
        self.stop()

    def detect_frame(self):
        """检测一帧图像
        
        返回:
            result: YOLO检测结果
            frame: 原始图像帧（未绘制标注）
        """
        self.target_detected = False 
        frame = self.picam2.capture_array() #通过树莓派摄像头捕获一帧图像
        
        # 这是YOLO推理的核心代码，调用 model方法 
        # 也就是调用YOLO推理self.model = YOLO(model_path, task='detect')
        # 把结果读取到results中
        results = self.model(frame, imgsz=self.imgsz, conf=self.conf, verbose=False)
        result = results[0]  # 取第一个结果,因为我的代码一次只处理一张图片，即 result = results[0]
        
        # 更新性能统计
        self.frame_counts += 1
        self.total_inference_time += result.speed['inference']

        # 判定逻辑,主要是存储的被检测目标的框的数据
        # 这里主要是读取result.boxes中框的 宽和高 ，判断被检测目标是不是过大目标，是否过滤
        self.target_detected = False
        if len(result.boxes) > 0:
            # 遍历所有检测框，找到第一个符合尺寸要求的
            for i in range(len(result.boxes)):
                x, y, w, h = result.boxes.xywh[i].tolist()
                
                #尺寸过滤,如果目标框的宽高都小于画面的55%，则认为是有效目标
                if w < 0.55 * self.SCREEN_WIDTH and h < 0.55 * self.SCREEN_HEIGHT:
                    self.target_detected = True
                    self.target_w, self.target_h = w, h
                    #更新中心点坐标，存在数据成员里面
                    self.target_center_x = x
                    self.target_center_y = y
                    
                    self.target_index = i  # 记录符合条件的框的索引
                    break  # 找到第一个就停止
            else:
                # 所有框都不符合尺寸要求
                self.target_detected = False
        
        # 直接返回原始帧，不绘制标注
        return result, frame
    
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
    
    def __enter__(self):
        """上下文管理器入口
        
        使用示例：
            with YOLODetector(MODEL_PATH) as detector:
                detector.start()
                # 使用检测器...
        """
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口
        
        自动调用 cleanup() 释放资源
        """
        self.cleanup()
        return False
    
    def __del__(self):
        """析构函数，确保资源释放
        
        防止忘记调用 cleanup() 导致资源泄漏
        """
        try:
            self.cleanup()
        except Exception:
            pass


# --- 单元测试 ---
if __name__ == "__main__":
    MODEL_PATH = "/home/pi/projects/yolo26/model_folder/ncnn_format_model/640_imgsz_ncnn_model/0207_quadcopter_yolo26_ncnn_model"
    
    # 方式1：使用with语句（推荐）
    print("=" * 50)
    print("测试1：使用 with 语句")
    print("=" * 50)
    with YOLODetector(MODEL_PATH) as detector:
        detector.start()
        try:
            for i in range(5):
                result, frame = detector.detect_frame()
                if detector.get_target_detected():
                    x, y = detector.get_target_center()
                    print(f"  测试 {i+1}: ✅ 目标检测到 - 中心: ({x:.1f}, {y:.1f})")
                else:
                    print(f"  测试 {i+1}: ❌ 未检测到目标")
                time.sleep(0.5)
        finally:
            # with 语句会自动调用 cleanup()，不需要手动写
            pass
    
    # 方式2：手动管理
    print("\n" + "=" * 50)
    print("测试2：手动管理")
    print("=" * 50)
    detector = YOLODetector(MODEL_PATH)
    detector.start()
    try:
        for i in range(5):
            result, frame = detector.detect_frame()
            if detector.get_target_detected():
                x, y = detector.get_target_center()
                print(f"  测试 {i+1}: ✅ 目标检测到 - 中心: ({x:.1f}, {y:.1f})")
            else:
                print(f"  测试 {i+1}: ❌ 未检测到目标")
            time.sleep(0.5)
    finally:
        detector.cleanup()  # 手动释放资源
    
    print("\n测试完成！")
