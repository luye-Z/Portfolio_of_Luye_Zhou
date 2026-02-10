import time
import math
from mpu6050 import mpu6050

# --- MPU6050 传感器处理类 ---
class SimpleMPU:
    def __init__(self, address, name):
        self.address = address
        self.name = name
        try:
            # 初始化 I2C 传感器实例
            self.sensor = mpu6050(address)
            # 电源管理寄存器 0x6B 写入 0x00：唤醒传感器（默认是休眠状态）
            self.sensor.bus.write_byte_data(self.address, 0x6b, 0x00)
            # 硬件唤醒需要极短的物理响应时间
            time.sleep(0.1) 
        except Exception as e:
            print(f"初始化 {self.name} 失败: {e}")
            raise e
        # 初始化偏移量字典，用于后续减去重力或安装误差
        self.offset = {'ax': 0, 'ay': 0, 'az': 0}

    def calibrate(self, samples=50):
        """ 校准：在静止状态下记录平均值，以此作为零点偏移 """
        print(f"正在校准 {self.name}...")
        ax, ay, az = 0, 0, 0
        for _ in range(samples):
            try:
                a = self.sensor.get_accel_data()
                ax+=a['x']; ay+=a['y']; az+=a['z']
            except OSError:
                continue
            time.sleep(0.005) # 校准阶段允许短暂阻塞，以保证采样频率稳定
        # 计算偏移量：Z轴减去 9.8 是因为重力加速度在静止时始终存在
        self.offset = {'ax': ax/samples, 'ay': ay/samples, 'az': (az/samples) - 9.8}

    def get_angles(self):
        """ 读取原始数据并转换为 俯仰角(Pitch) 和 横滚角(Roll) """
        try:
            a = self.sensor.get_accel_data()
            # 原始值减去校准后的偏移量
            cx = a['x'] - self.offset['ax']
            cy = a['y'] - self.offset['ay']
            cz = a['z'] - self.offset['az']
            
            # 使用数学公式计算角度
            # Pitch: 绕Y轴旋转的角度；Roll: 绕X轴旋转的角度
            pitch = math.degrees(math.atan2(cx, math.sqrt(cy**2 + cz**2)))
            roll = math.degrees(math.atan2(cy, cz))
            return pitch, roll
        except OSError:
            # 总线偶尔读取失败时返回 0，防止主程序崩溃
            return 0.0, 0.0

# --- 主程序入口 ---
if __name__ == "__main__":
    # 初始化双传感器
    mpu_a = SimpleMPU(0x68, "A")
    mpu_b = SimpleMPU(0x69, "B")
    
    # 启动前执行校准（必须保持静止）
    mpu_a.calibrate()
    mpu_b.calibrate()

    # --- 非阻塞控制核心变量 ---
    last_sample_time = 0      # 记录上一次读取传感器数据的时间戳
    sample_interval = 0.1     # 采样间隔：100毫秒（即 10Hz 频率）
    start_time = time.time()  # 记录程序启动的绝对时间

    print("\n[非阻塞模式启动] 系统已就绪...")

    try:
        # 这是一个“死循环”，但由于没有 time.sleep()，它会以极高速度运行
        while True:
            current_time = time.time()      # 获取当前精确时间
            elapsed = current_time - start_time  # 计算程序已运行的总时长
            phase = elapsed % 10            # 周期计算：10秒为一个循环周期

            # --- 逻辑层 1：大周期管理 (5s运行/5s停止) ---
            if phase < 5:
                # --- 逻辑层 2：高频采样控制 (非阻塞延时) ---
                # 检查当前时间与上次干活的时间差，是否达到了预设的 0.1s
                if current_time - last_sample_time >= sample_interval:
                    pa, ra = mpu_a.get_angles()
                    pb, rb = mpu_b.get_angles()
                    
                    # \r 表示回到行首打印，实现原地刷新效果
                    print(f"[RUNNING] A: {pa:>5.1f}/{ra:>5.1f} | B: {pb:>5.1f}/{rb:>5.1f}    ", end='\r')
                    
                    # 更新“上次干活时间”，为下一次 0.1s 后的操作做准备
                    last_sample_time = current_time
            else:
                # --- 逻辑层 3：静默周期处理 ---
                wait_time = 10 - phase
                print(f"[STOPPED] 正在休息，将在 {wait_time:.1f}s 后自动唤醒...    ", end='\r')

            # --- 逻辑层 4：空闲任务区 ---
            # CPU 在不读传感器时会运行到这里。你可以在这里添加 YOLO 推理、网络通信等。
            # 因为没有 sleep()，这里的代码响应速度是微秒级的。
            pass 
            
    except KeyboardInterrupt:
        print("\n程序停止")