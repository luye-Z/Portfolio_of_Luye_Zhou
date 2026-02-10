import time
import math
from mpu6050 import mpu6050

#添加了非阻塞延时功能


class SimpleMPU:
    def __init__(self, address, name):
        self.address = address
        self.name = name
        try:
            self.sensor = mpu6050(address)
            self.sensor.bus.write_byte_data(self.address, 0x6b, 0x00)
            # 这里初始化的微小延时是必须的，仅在启动时执行一次
            time.sleep(0.1) 
        except Exception as e:
            print(f"初始化 {self.name} 失败: {e}")
            raise e
        self.offset = {'ax': 0, 'ay': 0, 'az': 0}

    def calibrate(self, samples=50):
        print(f"正在校准 {self.name}...")
        ax, ay, az = 0, 0, 0
        for _ in range(samples):
            try:
                a = self.sensor.get_accel_data()
                ax+=a['x']; ay+=a['y']; az+=a['z']
            except OSError:
                continue
            time.sleep(0.005) # 仅校准时阻塞
        self.offset = {'ax': ax/samples, 'ay': ay/samples, 'az': (az/samples) - 9.8}

    def get_angles(self):
        try:
            a = self.sensor.get_accel_data()
            cx, cy, cz = a['x']-self.offset['ax'], a['y']-self.offset['ay'], a['z']-self.offset['az']
            pitch = math.degrees(math.atan2(cx, math.sqrt(cy**2 + cz**2)))
            roll = math.degrees(math.atan2(cy, cz))
            return pitch, roll
        except OSError:
            return 0.0, 0.0

if __name__ == "__main__":
    mpu_a = SimpleMPU(0x68, "A")
    mpu_b = SimpleMPU(0x69, "B")
    mpu_a.calibrate()
    mpu_b.calibrate()

    # --- 非阻塞变量初始化 ---
    last_sample_time = 0      # 上次采样的时间
    sample_interval = 0.1     # 采样频率 (0.1秒读一次)
    start_time = time.time()  # 程序运行起始时间

    print("\n[非阻塞模式启动] 你可以随时在循环中加入其他任务，不会被卡住")

    try:
        while True:
            current_time = time.time()
            elapsed = current_time - start_time
            phase = elapsed % 10  # 10秒一个周期

            # 1. 逻辑控制：判断是否在“运行 5 秒”的区间
            if phase < 5:
                # 2. 频率控制：判断是否到了采样点 (代替 time.sleep)
                if current_time - last_sample_time >= sample_interval:
                    pa, ra = mpu_a.get_angles()
                    pb, rb = mpu_b.get_angles()
                    
                    print(f"[RUNNING] A: {pa:>5.1f}/{ra:>5.1f} | B: {pb:>5.1f}/{rb:>5.1f}    ", end='\r')
                    
                    last_sample_time = current_time
            else:
                # 停止阶段：只打印倒计时，不读取传感器
                wait_time = 10 - phase
                print(f"[STOPPED] 正在休息，将在 {wait_time:.1f}s 后自动唤醒...    ", end='\r')

            # --- 这里可以放你的其他高贵代码 (比如 YOLO 检测) ---
            # 它会以极高的速度运行，完全不会被 MPU6050 的逻辑阻塞
            # do_yolo_inference() 
            
    except KeyboardInterrupt:
        print("\n程序停止")