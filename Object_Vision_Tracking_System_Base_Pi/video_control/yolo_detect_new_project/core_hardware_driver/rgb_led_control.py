import board
import neopixel
import time

class LEDController:
    def __init__(self, pin=board.D18, brightness=0.2):
        """
        针对单颗 WS2812B LED 的控制器
        :param pin: 数据引脚 (推荐 GPIO 18)
        :param brightness: 亮度 (0.0 到 1.0)
        """
        # 强制设置 num_pixels 为 1
        self.pixel = neopixel.NeoPixel(
            pin, 1, brightness=brightness, auto_write=True, pixel_order=neopixel.GRB
        )
        
        self.colors = {
            "red": (255, 0, 0),
            "green": (0, 255, 0),
            "blue": (0, 0, 255),
            "yellow": (255, 255, 0),
            "magenta": (255, 0, 255),
            "cyan": (0, 255, 255),
            "white": (255, 255, 255),
            "off": (0, 0, 0)
        }
        self.off()

    def set_color_rgb(self, r, g, b):
        """直接设置灯珠颜色"""
        self.pixel[0] = (r, g, b)

    def set_color_name(self, color_name):
        """根据名称设置颜色"""
        color = self.colors.get(color_name.lower())
        if color:
            self.set_color_rgb(*color)
        else:
            print(f"Unknown color: {color_name}")

    def off(self):
        """熄灭灯珠"""
        self.set_color_rgb(0, 0, 0)

    def cleanup(self):
        """退出清理"""
        self.off()
        print("LED released.")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

# --- 极简单测 ---
if __name__ == "__main__":
    print("Testing single WS2812B LED...")
    with LEDController() as led:
        test_colors = ["red", "green", "blue", "yellow", "white", "off"]
        for name in test_colors:
            print(f"Current color: {name}")
            led.set_color_name(name)
            time.sleep(0.8)