import time
import board
import busio
import adafruit_vl53l0x
import RPi.GPIO as GPIO

# --- 引脚定义 ---
XSHUT_PIN = 17  # 对应传感器的 XSHUT (使能引脚)
# 如果使用 Adafruit 库，通常直接通过 I2C 读取即可，
# 若仍需物理中断，可保留 INT_PIN，但初学者建议先跑通 I2C 连续模式

# --- 硬件初始化 ---
GPIO.setmode(GPIO.BCM)
GPIO.setup(XSHUT_PIN, GPIO.OUT)

# 1. 硬件复位传感器 (先低再高)
GPIO.output(XSHUT_PIN, GPIO.LOW)
time.sleep(0.1)
GPIO.output(XSHUT_PIN, GPIO.HIGH)
time.sleep(0.1)

# 2. 初始化 I2C 总线
try:
    i2c = busio.I2C(board.SCL, board.SDA)
    # 实例化传感器
    vl53 = adafruit_vl53l0x.VL53L0X(i2c)
    
    # 3. 配置参数 (可选)
    # 调整测量预算（Timing Budget），单位为微秒。
    # 20000 = 高速模式 (约 50Hz), 200000 = 高精度模式
    vl53.measurement_timing_budget = 20000 
    
    print("VL53L0X 初始化成功！")
except Exception as e:
    print(f"初始化失败，请检查接线或 I2C 是否开启: {e}")
    exit()

# --- 主循环 (集成 YOLO 逻辑) ---
print("开始测距... 配合 YOLO 运行中...")

try:
    while True:
        # 在这里执行你的 YOLO 识别
        # results = model.predict(frame) ...
        
        # 读取距离 (单位为 mm)
        # .distance 会自动处理数据转换，如果超出量程会返回 None 或极大值
        dist = vl53.distance
        
        if dist is not None:
            print(f">>> 目标距离: {dist} mm")
        else:
            print(">>> 超出测量范围")

        # 为了不让打印信息刷屏，稍微延迟
        # 实际运行 YOLO 时，这个 sleep 可以去掉或设得极短
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\n用户停止程序...")

finally:
    # 善后处理
    GPIO.cleanup()
    print("硬件资源已释放")