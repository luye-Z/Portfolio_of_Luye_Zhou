import time
import sys
import math
from mpu6050 import mpu6050
from rpi_hardware_pwm import HardwarePWM

# =============================================================================
# MPU6050 传感器配置
# =============================================================================

MPU_ADDRESS = 0x68  # MPU6050 I2C地址

# 舵机配置
CHIP_ID = 0  # PWM芯片ID（根据ls结果）
TILT_CHANNEL = 1  # GPIO13 -> channel 1 (TILT俯仰)
PAN_CHANNEL = 0   # GPIO12 -> channel 0 (PAN横滚)

SERVO_STEP_DELAY = 0.01  # 舵机步进延迟（秒）

def set_angle(pwm_obj, angle):
    """将角度(-90到90)映射为硬件占空比(2.5到12.5)"""
    angle = max(-90, min(90, angle))
    duty = (angle + 90) * (10 / 180) + 2.5
    pwm_obj.change_duty_cycle(duty)

# =============================================================================
# MPU6050 传感器类
# =============================================================================

class MPU6050_Sensor:
    def __init__(self, address=MPU_ADDRESS, name="MPU6050"):
        """初始化MPU6050传感器"""
        self.address = address
        self.name = name
        try:
            # 初始化I2C传感器实例
            self.sensor = mpu6050(address)
            # 电源管理寄存器0x6B写入0x00：唤醒传感器（默认是休眠状态）
            self.sensor.bus.write_byte_data(self.address, 0x6B, 0x00)
            # 硬件唤醒需要极短的物理响应时间
            time.sleep(0.1) 
        except Exception as e:
            print(f"初始化 {self.name} 失败: {e}")
            raise e
        
        # 初始化偏移量字典，用于后续减去重力或安装误差
        self.offset = {'ax': 0, 'ay': 0, 'az': 0}
    
    def calibrate(self, samples=50):
        """校准：在静止状态下记录平均值，以此作为零点偏移"""
        print(f"正在校准 {self.name}...")
        ax, ay, az = 0, 0, 0
        for _ in range(samples):
            try:
                a = self.sensor.get_accel_data()
                ax+=a['x']; ay+=a['y']; az+=a['z']
            except OSError:
                continue
            time.sleep(0.005) # 校准阶段允许短暂阻塞，以保证采样频率稳定
        
        # 计算偏移量：Z轴减去9.8是因为重力加速度在静止时始终存在
        self.offset = {'ax': ax/samples, 'ay': ay/samples, 'az': (az/samples) - 9.8}
        print(f"{self.name} 校准完成！偏移量: ax={self.offset['ax']:.2f}, ay={self.offset['ay']:.2f}, az={self.offset['az']:.2f}")
    
    def get_angles(self):
        """读取原始数据并转换为俯仰角(Pitch)和横滚角(Roll)"""
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
            # 总线偶尔读取失败时返回0，防止主程序崩溃
            return 0.0, 0.0

# =============================================================================
# 舵机控制文件路径
# =============================================================================

SERVO_CONTROL_FILE = "/home/pi/projects/yolo26/hardware_pwm_servos_driver/pwm_hardware.py"

# =============================================================================
# 主程序
# =============================================================================

def main():
    try:
        # 初始化MPU6050传感器
        print("正在初始化MPU6050传感器...")
        mpu = MPU6050_Sensor(address=MPU_ADDRESS, name="MPU6050")
        
        # 启动前执行校准（必须保持静止）
        print("请保持传感器静止，开始校准...")
        time.sleep(2)  # 给用户2秒时间准备
        mpu.calibrate()
        
        print("校准完成！开始读取传感器数据...")
        
        # 非阻塞控制核心变量
        last_sample_time = 0
        sample_interval = 0.1     # 采样间隔：100毫秒（即10Hz采样率）
        start_time = time.time()
        
        print("\n[非阻塞模式启动] 系统已就绪...")
        print("MPU6050传感器正在持续读取数据...")
        print("按 Ctrl+C 停止程序")
        
        try:
            # 这是一个"死循环"，但由于没有time.sleep()，它会以极高速度运行
            while True:
                current_time = time.time()
                elapsed = current_time - start_time
                phase = elapsed % 10            # 周期计算：10秒为一个循环周期
                
                # 逻辑层1：大周期管理 (5s运行/5s停止)
                if phase < 5:
                    # 逻辑层2：高频采样控制 (非阻塞延时)
                    # 检查当前时间与上次采样时间差，是否达到了预设的0.1s
                    if current_time - last_sample_time >= sample_interval:
                        pitch, roll = mpu.get_angles()
                        
                        # \r表示回到行首打印，实现原地刷新效果
                        print(f"[RUNNING] Pitch: {pitch:>5.1f}° | Roll: {roll:>5.1f}    ", end='\r')
                        
                        # 更新"上次采样时间"，为下一次0.1s后的操作做准备
                        last_sample_time = current_time
                else:
                    # 逻辑层3：静默周期处理
                    wait_time = 10 - phase
                    print(f"[STOPPED] 正在休息，将在 {wait_time:.1f}s 后自动唤醒...    ", end='\r')
                    
                # 逻辑层4：空闲任务区
                # CPU在不读传感器时会运行到这里。你可以在这里添加YOLO推理、网络通信等。
                # 因为没有sleep()，这里的代码响应速度是微秒级的。
                pass 
                
        except KeyboardInterrupt:
            print("\n程序停止")
            
    except Exception as e:
        print(f"\n发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()