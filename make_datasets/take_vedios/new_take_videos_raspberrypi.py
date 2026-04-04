import time
import os
import glob
import re
from picamera2 import Picamera2, Preview 
from picamera2.encoders import H264Encoder
from picamera2.outputs import FfmpegOutput

def get_auto_filename(prefix="0404_videos_for_datasets", ext=".mp4"):
    """自动生成递增文件名"""
    files = glob.glob(f"{prefix}_*{ext}")
    max_idx = 0
    for f in files:
        match = re.search(rf"{prefix}_(\d+)\{ext}$", f)
        if match:
            idx = int(match.group(1))
            if idx > max_idx:
                max_idx = idx
    return f"{prefix}_{max_idx + 1}{ext}"

def record_video(duration=10, output_file="video.mp4", resolution=(1640, 1232), framerate=30):
    picam2 = Picamera2()
    
    # 【核心修改】：将 format 从 "RGB888" 改为 "XRGB8888"
    # 这能解决预览窗口报错不支持格式的问题，同时保持画质
    video_config = picam2.create_video_configuration(
        main={
            "size": resolution, 
            "format": "XRGB8888" 
        },
        controls={"FrameRate": framerate}
    )
    picam2.configure(video_config)
    
    # 启动硬件加速预览
    try:
        picam2.start_preview(Preview.QTGL)
    except Exception:
        print("QTGL预览不可用，尝试DRM模式...")
        picam2.start_preview(Preview.DRM)
        
    picam2.start()
    
    # 设置 H264 编码器 (10Mbps)
    encoder = H264Encoder(bitrate=10000000)
    output = FfmpegOutput(output_file)
    
    print(f"开始录制视频，时长: {duration}秒")
    print(f"分辨率: {resolution[0]}x{resolution[1]}, 帧率: {framerate}fps")
    print(f"输出文件: {output_file}")
    
    # 开始录制
    picam2.start_recording(encoder, output)
    
    # 录制期间程序保持运行
    time.sleep(duration)
    
    # 停止
    picam2.stop_recording()
    picam2.stop_preview()
    picam2.stop()
    picam2.close()
    
    print(f"录制完成！视频已保存到: {output_file}")
    if os.path.exists(output_file):
        print(f"文件大小: {os.path.getsize(output_file) / (1024*1024):.2f} MB")

if __name__ == "__main__":
    auto_output_file = get_auto_filename()
    record_video(
        duration=10,
        output_file=auto_output_file,
        resolution=(1640, 1232),
        framerate=30
    )