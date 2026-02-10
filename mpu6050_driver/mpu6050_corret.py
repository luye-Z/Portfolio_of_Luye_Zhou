import time
import math
from mpu6050 import mpu6050

class SimpleMPU:
    def __init__(self, address, name):
        self.address = address
        self.name = name
        try:
            self.sensor = mpu6050(address)
            # 显式唤醒传感器 (写入 0x00 到电源管理寄存器 0x6B)
            # 解决 [Errno 121] Remote I/O error 的关键步骤
            self.sensor.bus.write_byte_data(self.address, 0x6b, 0x00)
            time.sleep(0.1) # 给传感器一点反应时间
        except Exception as e:
            print(f"初始化 {self.name} (0x{address:02x}) 失败: {e}")
            raise e
            
        self.offset = {'ax': 0, 'ay': 0, 'az': 0, 'gx': 0, 'gy': 0, 'gz': 0}

    def calibrate(self, samples=100):
        print(f"正在校准 {self.name} (地址: {hex(self.address)})... 请静止放置")
        ax, ay, az, gx, gy, gz = 0, 0, 0, 0, 0, 0
        success_samples = 0
        
        for _ in range(samples):
            try:
                a = self.sensor.get_accel_data()
                g = self.sensor.get_gyro_data()
                ax+=a['x']; ay+=a['y']; az+=a['z']
                gx+=g['x']; gy+=g['y']; gz+=g['z']
                success_samples += 1
            except OSError:
                # 如果单次读取失败，略过本次采样
                continue
            time.sleep(0.005)
        
        if success_samples == 0:
            raise Exception(f"{self.name} 校准失败，无法读取数据")

        # 计算偏移平均值（Z轴减去标准重力加速 9.8，假设平放）
        self.offset = {
            'ax': ax/success_samples, 
            'ay': ay/success_samples, 
            'az': (az/success_samples) - 9.8, 
            'gx': gx/success_samples, 
            'gy': gy/success_samples, 
            'gz': gz/success_samples
        }
        print(f"{self.name} 校准完成!")

    def get_angles(self):
        try:
            a = self.sensor.get_accel_data()
            # 减去校准偏移
            curr_ax = a['x'] - self.offset['ax']
            curr_ay = a['y'] - self.offset['ay']
            curr_az = a['z'] - self.offset['az']

            # 计算俯仰 (Pitch) 和 横滚 (Roll)
            # 使用 atan2 处理弧度，并转换为角度
            pitch = math.atan2(curr_ax, math.sqrt(curr_ay**2 + curr_az**2))
            roll = math.atan2(curr_ay, curr_az)
            
            return math.degrees(pitch), math.degrees(roll)
        except OSError:
            # 读取失败时返回上一次的值或 0，防止主循环中断
            return 0.0, 0.0

# --- 主程序 ---
if __name__ == "__main__":
    try:
        # 1. 初始化两个传感器 (地址需与 i2cdetect 结果对应)
        mpu_a = SimpleMPU(0x68, "传感器_A")
        time.sleep(0.2) # 避开总线竞争
        mpu_b = SimpleMPU(0x69, "传感器_B")

        # 2. 校准过程
        mpu_a.calibrate()
        mpu_b.calibrate()

        print("\n开始读取数据 (按 Ctrl+C 停止)...")
        print("传感器A (俯仰/横滚) | 传感器B (俯仰/横滚)")
        print("-" * 50)

        while True:
            pa, ra = mpu_a.get_angles()
            pb, rb = mpu_b.get_angles()
            
            # 使用 \r 实现单行刷新显示
            print(f"A: {pa:>6.1f}/{ra:>6.1f}  | B: {pb:>6.1f}/{rb:>6.1f} ", end='\r')
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n程序已由用户停止")
    except Exception as e:
        print(f"\n运行错误: {e}")
        print(f"\n运行错误: {e}")