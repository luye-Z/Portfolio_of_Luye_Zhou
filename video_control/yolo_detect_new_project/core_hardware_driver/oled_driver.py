from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import ImageFont
import time

class OLEDDriver:
    def __init__(self, port=1, address=0x3C, width=128, height=64):
        self.serial = i2c(port=port, address=address)
        self.device = ssd1306(self.serial, width=width, height=height)
        
        # 使用 PIL 的默认字体，避免找不到字体的问题
        self.font = ImageFont.load_default()
    
    def show_text(self, text, size=12, x=10, y=1):
        """在屏幕上显示文本"""
        # 忽略 size 参数，使用默认字体
        with canvas(self.device) as draw:
            draw.text((x, y), text, font=self.font, fill="white")
    
    def cleanup(self):
        self.device.cleanup()
        
        
if __name__ == "__main__":
    
    oled = OLEDDriver()
    try:
        oled.show_text("Hello, OLED!", size=12)
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        oled.cleanup()