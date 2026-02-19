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
        self.off() # 初始化为关闭状态

    def set_color(self, r, g, b):
        """设置全灯带为统一颜色 (0-255)"""
        self.pixels.fill((r, g, b))
        self.pixels.show()

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
        try:
            # 1. 基础颜色循环测试
            colors = [
                (255, 0, 0),   # 红
                (0, 255, 0),   # 绿
                (0, 0, 255),   # 蓝
                (255, 255, 0)  # 黄
            ]
            
            for c in colors:
                print(f"Setting color to RGB{c}")
                led.set_color(*c)
                time.sleep(0.5)

            # 2. 逐个点亮测试 (流水灯效果)
            print("Running Chase effect...")
            led.off()
            for i in range(led.num_pixels):
                led.set_pixel(i, 255, 100, 0) # 橙色点亮
                time.sleep(0.1)
            
            # 3. 非阻塞彩虹步进测试 (模拟主循环)
            print("Running Rainbow step test (Non-blocking)...")
            for step in range(255):
                led.rainbow_step(step)
                time.sleep(0.01) # 模拟 100FPS 的主循环速度

            print("Test Completed Successfully!")

        except KeyboardInterrupt:
            print("\nTest interrupted by user.")