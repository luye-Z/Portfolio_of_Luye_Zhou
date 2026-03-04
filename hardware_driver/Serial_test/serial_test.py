import serial
import time

# ==========================================
# 硬件配置参数
# ==========================================
# /dev/serial0 是树莓派 GPIO 串口的通用映射路径
# 经过底层配置(miniuart-bt)，此路径已指向高性能硬件串口 ttyAMA0
PORT = "/dev/serial0" 
BAUD_RATE = 9600      # 波特率必须与 ESP8266 SoftwareSerial 设置保持一致

try:
    # 初始化串口对象
    # timeout=1 表示读取操作在 1 秒后若无数据则返回，防止程序永久卡死
    ser = serial.Serial(PORT, BAUD_RATE, timeout=1)
    
    # 清空串口输入缓冲区，防止读取到之前残留的过期数据
    ser.reset_input_buffer()
    
    print(f"系统提示: 树莓派串口通信环境初始化成功 ({PORT})")
    print("------------------------------------------------")
except Exception as e:
    print(f"关键错误: 无法初始化串口硬件，请检查引脚权限或占用情况: {e}")
    exit()

# 计数器：用于追踪发送的数据包编号，便于分析丢包率
counter = 0

try:
    while True:
        # 1. 指令构造与编码
        # 串口传输的是字节流(Bytes)，因此需要将字符串通过 utf-8 编码
        # \n 作为结束符，方便 ESP8266 使用 readStringUntil('\n') 快速捕获
        send_msg = f"PI_DATA_{counter}\n"
        ser.write(send_msg.encode('utf-8'))
        
        # 打印本地发送日志（.strip() 用于去除末尾换行符以便于美观显示）
        print(f"本地输出 -> 正在发送指令: {send_msg.strip()}")

        # 2. 响应等待机制
        # 给物理层信号传输及下位机逻辑处理留出 100ms 的缓冲时间
        time.sleep(0.1) 

        # 3. 响应捕获与解码
        # 检查缓冲区中待读取的字节数
        if ser.in_waiting > 0:
            try:
                # readline() 读取一行，直到捕获到换行符
                response = ser.readline().decode('utf-8').strip()
                print(f"下位机响应 <- {response}")
            except UnicodeDecodeError:
                # 若电平不稳或未共地(GND)，会导致数据位翻转，引发解码错误
                print("警报: 捕获到非法字节流（乱码），请检查物理连接是否共地(GND)")

        # 步进更新
        counter += 1
        
        # 采样频率控制：每 2 秒进行一次完整的“请求-响应”循环
        time.sleep(2)

except KeyboardInterrupt:
    # 捕获 Ctrl+C 信号，优雅地关闭串口资源，防止再次运行时提示设备占用
    ser.close()
    print("\n用户中断: 串口连接已安全释放。")