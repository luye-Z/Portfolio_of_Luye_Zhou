import serial
import time
#PI to ESP 串口通信测试脚本
# 经过自检验证，/dev/serial0 是最稳定的路径
# 波特率统一设为 9600
port = "/dev/serial0"
baud = 9600

try:
    ser = serial.Serial(port, baud, timeout=1)
    ser.reset_input_buffer()
    print(f"--- 树莓派串口通信启动 ({port}) ---")
except Exception as e:
    print(f"无法打开串口: {e}")
    exit()

counter = 0
try:
    while True:
        # 1. 构造并发送数据
        send_msg = f"PI_DATA_{counter}\n"
        ser.write(send_msg.encode('utf-8'))
        print(f"发送 -> {send_msg.strip()}")

        # 2. 等待接收响应
        time.sleep(0.1)  # 给硬件一点处理时间
        if ser.in_waiting > 0:
            try:
                response = ser.readline().decode('utf-8').strip()
                print(f"接收 <- {response}")
            except UnicodeDecodeError:
                print("接收到乱码，请检查 GND 是否接牢")

        counter += 1
        time.sleep(2)

except KeyboardInterrupt:
    ser.close()
    print("\n通信停止")