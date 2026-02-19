import time
import board
import adafruit_sht4x

# 初始化 I2C 总线
i2c = board.I2C()  # 使用默认的 SCL 和 SDA 针脚

# 初始化 SHT40 传感器
# 默认 I2C 地址通常为 0x44
sht = adafruit_sht4x.SHT4x(i2c)

print("正在获取 SHT40 数据...")
print(f"传感器序列号: {hex(sht.serial_number)}")

# 你可以设置测量精度 (可选)
# sht.mode = adafruit_sht4x.Mode.NOHEAT_HIGHPRECISION

try:
    while True:
        # 读取温度和湿度
        temperature, relative_humidity = sht.measurements
        
        # 格式化输出
        print("\n" + "-"*20)
        print(f"温度: {temperature:.2f} °C")
        print(f"湿度: {relative_humidity:.2f} %")
        
        time.sleep(2)

except KeyboardInterrupt:
    print("\n程序已停止")