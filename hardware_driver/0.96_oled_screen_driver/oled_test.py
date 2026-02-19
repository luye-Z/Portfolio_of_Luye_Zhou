import os
import time
import threading
from PIL import Image, ImageSequence
from PIL import ImageFont, ImageDraw
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306

#配置IIC总线；在树莓派上port = 0 表示第一个IIC总线的端口号，port = 1 表示第二个IIC总线的端口号
serial = i2c(port = 1,address = 0x3C)
#创建一个 SSD1306 驱动器的对象 device，并且指定了硬件参数 serial、宽度和高度。
device = ssd1306(serial,width = 128,height = 64)

# SSD1312将视图反转
#device.command(0x00)  # 0xA0指令设置为默认的column address 0.
#device.command(0xA0)  # 0xA7指令打开像素反转

#用于在 OLED 屏幕上居中渲染指定文本的函数
def draw_text(text,width,height,fontsize):
        #加载 “arial.ttf”字体，font 字体对象，用于在 OLED 屏幕上渲染文字。
        font = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc", fontsize)
        #定义一个上下文管理器，canvas()函数返回一个绘制图像的对象 draw；
        #在这个上下文环境中，可以直接使用 OLED 显示屏的对象 device 进行屏幕绘制操作。
        #下文管理器是指遵循特殊协议的对象，具有 __enter__(self) 和 __exit__(self, exception_type, exception_value, traceback) 方法。
        # 这些方法被执行的顺序是：首先执行 __enter__() 方法，在上下文执行完毕后执行 __exit__() 方法。
        # （常见的上下文管理器包括文件对象、锁、数据库连接等等。）
        #with canvas(device) as draw:等价于：
        #draw = canvas(device)
        #try:
        # 在这里执行绘制操作
        #finally:
        #    draw.close()
        with canvas(device) as draw:
                #绘制了一个大小与 OLED 屏幕相同的黑色矩形，且边框使用白色进行绘制。
                draw.rectangle(device.bounding_box,outline="white",fill="black")
                #计算文本行的宽度
                w = font.getlength(text)
                #则用于计算字体的总高度（包括上坡度和下坡度）和下坡度。
                ascent,descent = font.getmetrics()
                #计算文本高度
                h = ascent - descent
                #计算文本X坐标
                x = (width - w)
                #计算文本y坐标
                y = (height -h)
                #draw.text() 在指定的坐标位置 (10, 1) 绘制了居中显示的文本内容。fill 参数用于指定文本绘制颜色，此处为白色。
                draw.text((10,1),text,font = font,fill = "white")
                
if __name__ == '__main__':
        while True:
            #调用draw_text函数显示文本;
            #device.width,device.height是luma.oled device的属性，其值是device = ssd1306(serial,width = 64,height = 128)在这里定义的高度和宽度
            draw_text("禄也，您好\n",device.width,device.height,12)
            print(f"屏幕正在显示：“禄也，您好”")
            time.sleep(2)