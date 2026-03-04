import serial
import time
import os

# 树莓派常见的串口设备路径
ports = ['/dev/serial0', '/dev/ttyS0', '/dev/ttyAMA0']
test_message = "PI_LOOPBACK_TEST_DATA\n"

def run_test(port_path):
    print(f"\n--- 正在测试串口: {port_path} ---")
    try:
        # 初始化串口：9600波特率，超时1秒
        with serial.Serial(port_path, 9600, timeout=1) as ser:
            print(f"成功打开 {port_path}")
            
            # 清空输入缓冲区
            ser.reset_input_buffer()
            
            # 发送测试数据
            ser.write(test_message.encode('utf-8'))
            print(f"已发送: {test_message.strip()}")
            
            # 等待一会确保数据传输完成
            time.sleep(0.1)
            
            # 读取返回数据
            if ser.in_waiting > 0:
                response = ser.readline().decode('utf-8').strip()
                if response == test_message.strip():
                    print(f"✅ 成功！收到匹配的回环数据: {response}")
                    return True
                else:
                    print(f"⚠️ 收到异常数据: {response}")
            else:
                print("❌ 未收到任何数据。请检查 Pin 8 和 Pin 10 是否已短接。")
                
    except Exception as e:
        print(f"🚫 无法访问 {port_path}: {e}")
    return False

if __name__ == "__main__":
    print("开始树莓派串口物理回环自检...")
    print("注意：请确保 Pin 8 (TX) 和 Pin 10 (RX) 已用跳线短接！")
    
    results = []
    for p in ports:
        if os.path.exists(p):
            results.append(run_test(p))
        else:
            print(f"跳过 {p} (设备不存在)")

    if any(results):
        print("\n结论：树莓派串口硬件与驱动正常！可以连接 ESP8266 进行实验。")
    else:
        print("\n结论：所有串口均未通过回环测试。请检查 raspi-config 设置或硬件引脚。")