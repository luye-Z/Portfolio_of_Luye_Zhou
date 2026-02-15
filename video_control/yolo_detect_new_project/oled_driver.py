import os
import time
import threading
from PIL import Image, ImageFont, ImageDraw
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306


class OLEDDisplay:
    """
    OLED屏幕显示类
    用于在SSD1306 OLED屏幕上显示文本，支持多线程非阻塞显示
    """
    
    def __init__(self, port=1, address=0x3C, width=128, height=64, font_path="/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"):
        """
        初始化OLED显示器
        
        Args:
            port (int): IIC总线端口号，树莓派上0表示第一个IIC总线，1表示第二个IIC总线
            address (hex): IIC设备地址，默认0x3C
            width (int): 屏幕宽度，默认128像素
            height (int): 屏幕高度，默认64像素
            font_path (str): 字体文件路径
        """
        self.port = port
        self.address = address
        self.width = width
        self.height = height
        self.font_path = font_path
        
        # 初始化IIC和OLED设备
        self.serial = i2c(port=self.port, address=self.address)
        self.device = ssd1306(self.serial, width=self.width, height=self.height)
        
        # 线程相关
        self.display_thread = None
        self.is_running = False
        self.current_text = ""
        self.current_fontsize = 12
        self.current_duration = 2
        
        # 线程锁，用于保护共享资源
        self.lock = threading.Lock()
    
    def _draw_text(self, text, fontsize):
        """
        在OLED屏幕上绘制文本（内部方法）
        
        Args:
            text (str): 要显示的文本
            fontsize (int): 字体大小
        """
        try:
            font = ImageFont.truetype(self.font_path, fontsize)
            
            with canvas(self.device) as draw:
                # 绘制黑色背景和白色边框
                draw.rectangle(self.device.bounding_box, outline="white", fill="black")
                
                # 计算文本宽度和高度
                w = font.getlength(text)
                ascent, descent = font.getmetrics()
                h = ascent - descent
                
                # 计算居中坐标
                x = (self.width - w) / 2
                y = (self.height - h) / 2
                
                # 绘制文本
                draw.text((x, y), text, font=font, fill="white")
        except Exception as e:
            print(f"绘制文本出错: {e}")
    
    def _display_worker(self):
        """
        线程工作函数，持续显示内容
        """
        while self.is_running:
            with self.lock:
                text = self.current_text
                fontsize = self.current_fontsize
                duration = self.current_duration
            
            if text:
                # 显示文本
                self._draw_text(text, fontsize)
                print(f"屏幕正在显示: {text}")
                
                # 显示持续时间
                time.sleep(duration)
            else:
                # 如果没有内容，短暂休眠避免CPU占用
                time.sleep(0.1)
    
    def start(self):
        """
        启动显示线程
        """
        if not self.is_running:
            self.is_running = True
            self.display_thread = threading.Thread(target=self._display_worker, daemon=True)
            self.display_thread.start()
            print("OLED显示线程已启动")
    
    def stop(self):
        """
        停止显示线程
        """
        self.is_running = False
        if self.display_thread is not None and self.display_thread.is_alive():
            self.display_thread.join(timeout=2)
            print("OLED显示线程已停止")
    
    def display_text(self, text, fontsize=12, duration=2):
        """
        显示文本（非阻塞）
        
        Args:
            text (str): 要显示的文本
            fontsize (int): 字体大小，默认12
            duration (float): 显示时长（秒），默认2秒
        """
        if not self.is_running:
            self.start()
        
        with self.lock:
            self.current_text = text
            self.current_fontsize = fontsize
            self.current_duration = duration
    
    def clear(self):
        """
        清空屏幕
        """
        try:
            with canvas(self.device) as draw:
                draw.rectangle(self.device.bounding_box, outline="white", fill="black")
            print("屏幕已清空")
        except Exception as e:
            print(f"清空屏幕出错: {e}")
    
    def __enter__(self):
        """
        上下文管理器入口
        """
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        上下文管理器出口
        """
        self.stop()
        self.clear()


if __name__ == '__main__':
    # 使用方式1：直接调用
    display = OLEDDisplay()
    display.start()
    
    # 主程序可以继续执行其他操作，不会被阻塞
    for i in range(5):
        display.display_text(f"禄也，您好 {i}", fontsize=12, duration=2)
        print(f"主程序继续执行... {i}")
        time.sleep(1)
    
    display.stop()
    
    # 使用方式2：上下文管理器（推荐）
    # with OLEDDisplay() as display:
    #     for i in range(5):
    #         display.display_text(f"禄也，您好 {i}", fontsize=12, duration=2)
    #         print(f"主程序继续执行... {i}")
    #         time.sleep(1)