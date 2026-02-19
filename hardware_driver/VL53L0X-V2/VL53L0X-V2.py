import time
from smbus2 import SMBus

class VL53L0X_Lite:
    def __init__(self, address=0x29, bus_id=1):
        self.address = address
        self.bus = SMBus(bus_id)
        self._setup()

    def _setup(self):
        """基本的寄存器初始化序列"""
        # 设置基本功率和模式 (参考 ST 官方数据手册的最小启动序列)
        self.bus.write_byte_data(self.address, 0x88, 0x00)
        self.bus.write_byte_data(self.address, 0x80, 0x01)
        self.bus.write_byte_data(self.address, 0xFF, 0x01)
        self.bus.write_byte_data(self.address, 0x00, 0x00)
        
        # 停止当前的测量
        self.bus.write_byte_data(self.address, 0x91, 0x3c)
        self.bus.write_byte_data(self.address, 0x00, 0x01)
        self.bus.write_byte_data(self.address, 0xFF, 0x00)
        self.bus.write_byte_data(self.address, 0x80, 0x00)

    def get_distance(self):
        """执行单次测量并读取数据"""
        # 触发测量 (0x01 = SYSRANGE_START)
        self.bus.write_byte_data(self.address, 0x00, 0x01)
        
        # 等待数据准备就绪 (简单的轮询)
        # 在正式生产环境建议加入超时判断
        count = 0
        while (self.bus.read_byte_data(self.address, 0x14) & 0x01) == 0:
            time.sleep(0.01)
            count += 1
            if count > 100: return -1 # 超时
            
        # 读取 12 字节的数据 (从寄存器 0x14 开始读取距离结果)
        # 结果在 0x1E (高位) 和 0x1F (低位)
        data = self.bus.read_i2c_block_data(self.address, 0x14, 12)
        dist = (data[10] << 8) | data[11]
        
        # 清除中断标志位
        self.bus.write_byte_data(self.address, 0x0B, 0x01)
        
        return dist

# --- 测试代码 ---
if __name__ == "__main__":
    try:
        sensor = VL53L0X_Lite()
        print("VL53L0X 底层驱动测试 (无第三方依赖)")
        while True:
            d = sensor.get_distance()
            if d > 20: # 过滤掉极近距离的干扰值
                print(f"距离: {d} mm")
            else:
                print("未检测到物体")
            time.sleep(0.2)
    except Exception as e:
        print(f"错误: {e}")