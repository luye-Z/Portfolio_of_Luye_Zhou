from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import ImageFont

class OLEDDriver:
    def __init__(self, port=1, address=0x3C, width=128, height=64):
        self.serial = i2c(port=port, address=address)
        self.device = ssd1306(self.serial, width=width, height=height)
        # 加载中文字体
        self.font_path = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"
        
    def show_text(self, text, size=12, x=10, y=1):
        """在屏幕上显示文本"""
        font = ImageFont.truetype(self.font_path, size)
        with canvas(self.device) as draw:
            # 绘制边框和填充背景
            draw.rectangle(self.device.bounding_box, outline="white", fill="black")
            # 绘制文本（支持换行）
            draw.text((x, y), text, font=font, fill="white")

    def clear(self):
        """清空屏幕"""
        self.device.clear()
        print("OLED 屏幕已清空")

    def cleanup(self):
        """释放资源"""
        self.clear()
        
if __name__ == "__main__":
    
    oled = OLEDDriver()
    try:
        while True:
            oled.show_text("Hello, OLED!\n你好，OLED！", size=12)
    except KeyboardInterrupt:
        oled.cleanup()