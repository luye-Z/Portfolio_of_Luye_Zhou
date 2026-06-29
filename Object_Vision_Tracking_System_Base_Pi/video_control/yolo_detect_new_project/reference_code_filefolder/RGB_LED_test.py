# RGB_LED型号 ：WS2812B-5050RGB
#树莓派5
#引脚GPIO18连接 RGB_LED的 DIN

import time
import board
import neopixel

# --- 配置参数 ---
# 引脚定义：GPIO 18
pixel_pin = board.D18

# LED灯珠的数量
num_pixels = 10 

# 亮度设置 (0.0 到 1.0)
ORDER = neopixel.GRB

# 初始化灯带
pixels = neopixel.NeoPixel(
    pixel_pin, num_pixels, brightness=0.2, auto_write=False, pixel_order=ORDER
)

def rainbow_cycle(wait):
    """彩虹循环效果"""
    for j in range(255):
        for i in range(num_pixels):
            pixel_index = (i * 256 // num_pixels) + j
            pixels[i] = colorwheel(pixel_index & 255)
        pixels.show()
        time.sleep(wait)

def colorwheel(pos):
    """生成彩虹颜色"""
    if pos < 0 or pos > 255:
        r = g = b = 0
    elif pos < 85:
        r = int(pos * 3)
        g = int(255 - pos * 3)
        b = 0
    elif pos < 170:
        pos -= 85
        r = int(255 - pos * 3)
        g = 0
        b = int(pos * 3)
    else:
        pos -= 170
        r = 0
        g = int(pos * 3)
        b = int(255 - pos * 3)
    return (r, g, b)

try:
    print("开始测试：WS2812B (按 Ctrl+C 停止)")
    while True:
        # 1. 纯色测试

        print("红色")
        pixels.fill((255, 0, 0))  # 红色
        pixels.show()
        time.sleep(1)

        print("绿色")
        pixels.fill((0, 255, 0))  # 绿色
        pixels.show()
        time.sleep(1)

        print("蓝色")
        pixels.fill((0, 0, 255))  # 蓝色
        pixels.show()
        time.sleep(1)

        print("紫色")
        pixels.fill((128, 0, 128))  # 紫色
        pixels.show()
        time.sleep(1)

        print("黄色")
        pixels.fill((255, 255, 0))  # 黄色
        pixels.show()
        time.sleep(1)

        print("橙色")
        pixels.fill((255, 165, 0))  # 橙色
        pixels.show()
        time.sleep(1)

        print("粉色")
        pixels.fill((255, 192, 203))  # 粉色
        pixels.show()
        time.sleep(1)

        print("青色")
        pixels.fill((0, 255, 255))  # 青色
        pixels.show()
        time.sleep(1)

        print("深蓝色")
        pixels.fill((0, 0, 139))  # 深蓝色
        pixels.show()
        time.sleep(1)

        print("淡紫色")
        pixels.fill((230, 230, 250))  # 淡紫色
        pixels.show()
        time.sleep(1)

        print("淡蓝色")
        pixels.fill((173, 216, 230))  # 淡蓝色
        pixels.show()
        time.sleep(1)

        print("草绿色")
        pixels.fill((124, 252, 0))  # 草绿色
        pixels.show()
        time.sleep(1)

        print("玫瑰红")
        pixels.fill((255, 0, 127))  # 玫瑰红
        pixels.show()
        time.sleep(1)

        print("深红色")
        pixels.fill((139, 0, 0))  # 深红色
        pixels.show()
        time.sleep(1)

        print("天蓝色")
        pixels.fill((135, 206, 235))  # 天蓝色
        pixels.show()
        time.sleep(1)

        print("金色")
        pixels.fill((255, 215, 0))  # 金色
        pixels.show()
        time.sleep(1)

        print("浅绿色")
        pixels.fill((144, 238, 144))  # 浅绿色
        pixels.show()
        time.sleep(1)

        print("浅橙色")
        pixels.fill((255, 204, 153))  # 浅橙色
        pixels.show()
        time.sleep(1)


        # # 2. 彩虹循环
        # print("彩虹模式...")
        # for _ in range(3): # 循环3次
        #     rainbow_cycle(0.001)

except KeyboardInterrupt:
    # 退出时关闭所有灯光
    pixels.fill((0, 0, 0))
    pixels.show()
    print("\n测试结束")