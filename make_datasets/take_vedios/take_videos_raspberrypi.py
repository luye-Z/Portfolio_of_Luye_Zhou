import time
import os
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FfmpegOutput

def record_video(duration=10, output_file="video.mp4", resolution=(1920, 1080), framerate=30):
    """
    使用树莓派摄像头录制视频
    
    参数:
        duration: 录制时长（秒）
        output_file: 输出文件名
        resolution: 视频分辨率 (宽, 高)
        framerate: 帧率
    """
    # 初始化摄像头
    picam2 = Picamera2()
    
    # 配置视频录制
    video_config = picam2.create_video_configuration(
        main={"size": resolution, "format": "RGB888"},
        controls={"FrameRate": framerate}
    )
    picam2.configure(video_config)
    
    # 设置编码器
    encoder = H264Encoder(bitrate=10000000)  # 10Mbps
    output = FfmpegOutput(output_file)
    
    print(f"开始录制视频，时长: {duration}秒")
    print(f"分辨率: {resolution[0]}x{resolution[1]}, 帧率: {framerate}fps")
    print(f"输出文件: {output_file}")
    
    # 开始录制
    picam2.start_recording(encoder, output)
    
    # 录制指定时长
    time.sleep(duration)
    
    # 停止录制
    picam2.stop_recording()
    picam2.close()
    
    print(f"录制完成！视频已保存到: {output_file}")
    print(f"文件大小: {os.path.getsize(output_file) / (1024*1024):.2f} MB")

if __name__ == "__main__":
    # 示例：录制10秒视频
    record_video(
        duration=10,           # 录制10秒
        output_file="my_video.mp4",
        resolution=(1920, 1080),  # 1080p
        framerate=30           # 30fps
    )