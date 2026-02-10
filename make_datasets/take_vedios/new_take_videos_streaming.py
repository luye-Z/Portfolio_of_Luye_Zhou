import time
import os
import cv2
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FfmpegOutput

def record_video_with_preview(duration=10, output_file="0208_video_0.mp4", resolution=(1640, 1232), framerate=30):
    """
    使用树莓派摄像头录制视频，带实时预览（匹配YOLO预测脚本的视角）
    
    参数:
        duration: 录制时长（秒）
        output_file: 输出文件名
        resolution: 视频分辨率 (宽, 高) - 默认使用1640x1232以匹配预览配置
        framerate: 帧率
    """
    # 初始化摄像头
    picam2 = Picamera2()
    
    # 使用与预览相同的配置，确保视角一致
    video_config = picam2.create_video_configuration(
        main={
            "size": resolution, 
            "format": "RGB888"
        },
        controls={"FrameRate": framerate}
    )
    picam2.configure(video_config)
    
    # 设置编码器
    encoder = H264Encoder(bitrate=10000000)  # 10Mbps
    output = FfmpegOutput(output_file)
    
    print(f"开始录制视频，时长: {duration}秒")
    print(f"分辨率: {resolution[0]}x{resolution[1]}, 帧率: {framerate}fps")
    print(f"输出文件: {output_file}")
    print("按 'q' 键可提前结束录制")
    
    # 启动摄像头
    picam2.start()
    
    # 开始录制
    picam2.start_recording(encoder, output)
    
    # 记录开始时间
    start_time = time.time()
    
    try:
        while True:
            # 计算已录制时长
            elapsed_time = time.time() - start_time
            remaining_time = duration - elapsed_time
            
            # 如果超过录制时长，退出
            if elapsed_time >= duration:
                break
            
            # 捕获当前帧用于显示
            frame = picam2.capture_array()
            
            # 在画面上显示录制信息
            display_frame = frame.copy()
            
            # 显示录制时间
            time_text = f"Recording: {int(elapsed_time)}s / {duration}s"
            cv2.putText(display_frame, time_text, (30, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
            
            # 显示剩余时间
            remaining_text = f"Remaining: {int(remaining_time)}s"
            cv2.putText(display_frame, remaining_text, (30, 120), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
            
            # 显示录制标志（红点）
            cv2.circle(display_frame, (resolution[0] - 50, 50), 20, (0, 0, 255), -1)
            cv2.putText(display_frame, "REC", (resolution[0] - 130, 65), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            # 调整显示大小以适应屏幕（与你的YOLO脚本一样）
            cv2.imshow("Recording Video", cv2.resize(display_frame, (820, 616)))
            
            # 检查按键，按 'q' 提前退出
            if cv2.waitKey(1) == ord("q"):
                print("\n用户提前终止录制")
                break
                
    finally:
        # 停止录制
        picam2.stop_recording()
        picam2.stop()
        cv2.destroyAllWindows()
        
        print(f"\n录制完成！视频已保存到: {output_file}")
        print(f"实际录制时长: {elapsed_time:.2f}秒")
        
        # 检查文件是否存在后再显示大小
        if os.path.exists(output_file):
            print(f"文件大小: {os.path.getsize(output_file) / (1024*1024):.2f} MB")

if __name__ == "__main__":
    # 使用与YOLO预测脚本相同的分辨率 (1640, 1232)
    record_video_with_preview(
        duration=10,                    # 录制10秒
        output_file="my_0208_video0.mp4",
        resolution=(1640, 1232),        # 与camera_predict脚本相同的分辨率
        framerate=30                    # 30fps
    )
