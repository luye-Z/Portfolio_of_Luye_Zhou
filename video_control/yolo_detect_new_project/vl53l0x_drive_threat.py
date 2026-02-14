import time
import threading
from smbus2 import SMBus

class VL53L0X_Threaded:
    def __init__(self, address=0x29, bus_id=1):
        self.address = address
        try:
            self.bus = SMBus(bus_id)
        except Exception as e:
            print(f"[Sensor] 无法打开I2C总线: {e}")
            self.bus = None
            
        self._distance = -1      # 存储最新的距离数据
        self._running = False    # 线程运行标志
        self._setup()

    def _setup(self):
        """基本的寄存器初始化"""
        if not self.bus: return
        try:
            self.bus.write_byte_data(self.address, 0x88, 0x00)
            self.bus.write_byte_data(self.address, 0x80, 0x01)
            self.bus.write_byte_data(self.address, 0xFF, 0x01)
            self.bus.write_byte_data(self.address, 0x00, 0x00)
            self.bus.write_byte_data(self.address, 0x91, 0x3c)
            self.bus.write_byte_data(self.address, 0x00, 0x01)
            self.bus.write_byte_data(self.address, 0xFF, 0x00)
            self.bus.write_byte_data(self.address, 0x80, 0x00)
        except Exception as e:
            print(f"[Sensor] 初始化失败: {e}")

    def _update(self):
        """后台线程循环执行测量"""
        print("[Sensor] 测距线程已启动")
        while self._running:
            try:
                # 触发单次测量
                self.bus.write_byte_data(self.address, 0x00, 0x01)
                
                # 等待就绪
                count = 0
                while (self.bus.read_byte_data(self.address, 0x14) & 0x01) == 0:
                    time.sleep(0.005) # 缩小轮询间隔，提高响应
                    count += 1
                    if count > 50: break
                
                # 读取数据
                data = self.bus.read_i2c_block_data(self.address, 0x14, 12)
                self._distance = (data[10] << 8) | data[11]
                
                # 清除中断
                self.bus.write_byte_data(self.address, 0x0B, 0x01)
                
                # 控制采样频率，避免把I2C总线占满（约每秒20次）
                time.sleep(0.05)
                
            except Exception as e:
                # print(f"[Sensor] 读取错误: {e}")
                time.sleep(1) # 出错时等待稍长一点

    def start(self):
        """启动测距线程"""
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._update, daemon=True)
            self._thread.start()

    def stop(self):
        """停止测距线程"""
        self._running = False
        if hasattr(self, '_thread'):
            self._thread.join()

    @property
    def distance(self):
        """主程序通过此属性获取最新距离，无需等待"""
        return self._distance

# --- 主程序调用演示 ---
if __name__ == "__main__":
    sensor = VL53L0X_Threaded()
    sensor.start() # 启动后台测距
    
    try:
        while True:
            # 模拟主程序（如YOLO推理）
            # 这里拿到的 distance 是后台线程早就准备好的
            current_d = sensor.distance
            
            print(f"主程序正在运行... 当前探测距离: {current_d} mm")
            
            # 主程序哪怕 sleep 1秒，后台测距也在偷偷更新
            #不要在主程序加阻塞延时
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        sensor.stop()
        print("程序退出")