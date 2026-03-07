import math
import time
import threading
from mpu6050 import mpu6050

class MPU6050driver:
    
    def __init__(self, address=0x68, alpha=0.98):
        self.sensor = mpu6050(address)
        self.alpha = alpha  # 互补滤波系数
        self.offsets = {'ax': 0, 'ay': 0, 'az': 0, 'gx': 0, 'gy': 0, 'gz': 0}
        self.pitch = 0.0
        self.roll = 0.0
        self.last_time = None
        self.lock = threading.Lock()  # 用于同步数据访问
        
        #控制线程多长时间读取一下MPU6050的数据，单位S
        self.DATA_READ_TIME_STEP = 5
        
    def calibrate(self, samples=200):
        """精准校准，计算传感器静止时的偏置"""
        print(f"正在校准 MPU6050 ({samples} 次采样)，请保持传感器静止...")
        s = {'ax': 0, 'ay': 0, 'az': 0, 'gx': 0, 'gy': 0, 'gz': 0}
        for _ in range(samples):
            a = self.sensor.get_accel_data()
            g = self.sensor.get_gyro_data()
            s['ax'] += a['x']
            s['ay'] += a['y']
            s['az'] += (a['z'] - 9.80665)  # 减去重力加速度
            s['gx'] += g['x']
            s['gy'] += g['y']
            s['gz'] += g['z']
            time.sleep(0.005)
        
        self.offsets = {k: v / samples for k, v in s.items()}
        self.last_time = time.time()
        print("校准完成！")

    def get_pose(self):
        """获取当前姿态角 (pitch, roll)"""
        if self.last_time is None:
            self.last_time = time.time()
            return 0.0, 0.0

        # 1. 时间增量计算
        current_time = time.time()
        dt = current_time - self.last_time
        self.last_time = current_time

        # 2. 读取原始数据并扣除偏移
        accel = self.sensor.get_accel_data()
        gyro = self.sensor.get_gyro_data()
        
        ax = accel['x'] - self.offsets['ax']
        ay = accel['y'] - self.offsets['ay']
        az = accel['z'] - self.offsets['az']
        gx = gyro['x'] - self.offsets['gx']
        gy = gyro['y'] - self.offsets['gy']

        # 3. 计算加速度计观测角
        acc_p = math.degrees(math.atan2(ay, math.sqrt(ax**2 + az**2)))
        acc_r = math.degrees(math.atan2(-ax, az))

        # 4. 互补滤波融合
        # 陀螺仪积分（短期可靠）+ 加速度计修正（长期可靠）
        self.pitch = self.alpha * (self.pitch + gy * dt) + (1 - self.alpha) * acc_p
        self.roll = self.alpha * (self.roll + gx * dt) + (1 - self.alpha) * acc_r

        return self.pitch, self.roll
    
    def start_reading(self):
        """启动线程，获取姿态数据"""
        def read_data():
            while True:
                with self.lock:
                    self.pitch, self.roll = self.get_pose()
                    # print(f"Pitch: {pitch:.2f}°, Roll: {roll:.2f}°")
                time.sleep(self.DATA_READ_TIME_STEP)  # 控制数据读取频率

        # 启动数据读取线程
        threading.Thread(target=read_data, daemon=True).start()
        
    def get_mpu6050_angle_pose(self):
        return self.pitch, self.roll
        
    def cleanup(self):
        """释放资源：停止线程，清理状态"""
        print("\n正在关闭 MPU6050 资源...")
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0) # 等待线程结束
        print("MPU6050 线程已安全停止，I2C 总线已释放。")

if __name__ == "__main__":
    mpu = MPU6050driver()
    mpu.calibrate()
    mpu.start_reading()  # 启动线程读取数据
    
    # 主程序继续执行其他任务
    while True:
        # 主程序可以执行其他任务
        
        time.sleep(1)  # 示例的主程序工作
        
       
