from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import ImageFont
import time

class OLEDDriver:
    def __init__(self, port=1, address=0x3C, width=128, height=64):
        self.serial = i2c(port=port, address=address)
        self.device = ssd1306(self.serial, width=width, height=height)
        
        # ✅ 在初始化时就预加载字体，而不是每次都加载
        self.font_12 = ImageFont.truetype(
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc", 12
        )
        self.font_16 = ImageFont.truetype(
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc", 16
        )
    
    def show_text(self, text, size=12, x=10, y=1):
        """在屏幕上显示文本"""
        # 选择预加载的字体
        font = self.font_12 if size == 12 else self.font_16
        
        with canvas(self.device) as draw:
            draw.text((x, y), text, font=font, fill="white")
    
    def cleanup(self):
        self.device.cleanup()
        
        
if __name__ == "__main__":
    
    oled = OLEDDriver()
    try:
        oled.show_text("Hello, OLED!\n你好，OLED！", size=20)
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        oled.cleanup()