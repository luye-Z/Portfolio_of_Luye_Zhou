import board
import neopixel
import time

class LEDController:
    def __init__(self, pin=board.D18, num_pixels=10, brightness=0.2):
        """
        WS2812B LED 控制器
        :param pin: 数据引脚 (推荐 GPIO 18)
        :param num_pixels: 灯珠数量
        :param brightness: 初始亮度 (0.0 到 1.0)
        """
        self.num_pixels = num_pixels
        self.pixels = neopixel.NeoPixel(
            pin, 
            num_pixels, 
            brightness=brightness, 
            auto_write=False, 
            pixel_order=neopixel.GRB
        )
        self.off()  # 初始化为关闭状态

        # 定义常用颜色
        self.colors = {
            "red": (255, 0, 0),
            "green": (0, 255, 0),
            "blue": (0, 0, 255),
            "yellow": (255, 255, 0),
            "magenta": (255, 0, 255),
            "cyan": (0, 255, 255),
            "white": (255, 255, 255),
            "black": (0, 0, 0)
            }

    def set_color_rgb(self, r, g, b):
        """设置全灯带为统一颜色 (0-255)"""
        self.pixels.fill((r, g, b))
        self.pixels.show()
        
    def set_color_name(self, color_name):
        """设置全灯带为统一颜色 (颜色名称)"""
        if color_name in self.colors:
            self.set_color_rgb(*self.colors[color_name])
        else:
            print(f"颜色 {color_name} 不存在")

    def set_pixel(self, index, r, g, b):
        """设置单个灯珠颜色"""
        if 0 <= index < self.num_pixels:
            self.pixels[index] = (r, g, b)
            self.pixels.show()

    def rainbow_step(self, iteration):
        """
        彩虹单步变换 (方便集成在主循环中，不阻塞)
        :param iteration: 当前的时间步 (0-255)
        """
        for i in range(self.num_pixels):
            pixel_index = (i * 256 // self.num_pixels) + iteration
            self.pixels[i] = self._colorwheel(pixel_index & 255)
        self.pixels.show()

    def _colorwheel(self, pos):
        """内部颜色生成逻辑"""
        if pos < 85:
            return (int(pos * 3), int(255 - pos * 3), 0)
        elif pos < 170:
            pos -= 85
            return (int(255 - pos * 3), 0, int(pos * 3))
        else:
            pos -= 170
            return (0, int(pos * 3), int(255 - pos * 3))

    def off(self):
        """熄灭所有灯"""
        self.pixels.fill((0, 0, 0))
        self.pixels.show()

    def cleanup(self):
        """退出清理"""
        self.off()
        print("LED resources released.")

    # 上下文管理器支持
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
        
        
        
#单测       
if __name__ == "__main__":
    # --- 自动化单元测试逻辑 ---
    print("Starting LEDController Unit Test...")
    
    # 使用 with 语句确保即使报错也能安全关闭 LED
    with LEDController(num_pixels=10, brightness=0.2) as led:
        
        led.set_color_name("red")
        time.sleep(0.5)
        led.set_color_name("green")
        time.sleep(0.5)
        led.set_color_name("blue")
        time.sleep(0.5)
        led.set_color_name("yellow")
        time.sleep(0.5)
        led.set_color_name("magenta")
        time.sleep(0.5)
        led.set_color_name("cyan")
        time.sleep(0.5)
        led.set_color_name("white")
        time.sleep(0.5)
        led.set_color_name("black")
        time.sleep(0.5)