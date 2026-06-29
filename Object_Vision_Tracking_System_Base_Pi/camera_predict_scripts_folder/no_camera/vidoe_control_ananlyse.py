import time
from picamera2 import Picamera2
from ultralytics import YOLO
from rpi_hardware_pwm import HardwarePWM
import RPi.GPIO as GPIO
import threading
from smbus2 import SMBus

# =============================================================================
# VL53L0X 测距传感器类
# =============================================================================
class VL53L0X_Lite:
    def __init__(self, address=0x29, bus_id=1):
        self.address = address
        self.bus = SMBus(bus_id)
        self._setup()

    def _setup(self):
        """基本的寄存器初始化序列"""
        self.bus.write_byte_data(self.address, 0x88, 0x00)
        self.bus.write_byte_data(self.address, 0x80, 0x01)
        self.bus.write_byte_data(self.address, 0xFF, 0x01)
        self.bus.write_byte_data(self.address, 0x00, 0x00)
        self.bus.write_byte_data(self.address, 0x91, 0x3c)
        self.bus.write_byte_data(self.address, 0x00, 0x01)
        self.bus.write_byte_data(self.address, 0xFF, 0x00)
        self.bus.write_byte_data(self.address, 0x80, 0x00)

    def get_distance(self):
        """执行单次测量并读取数据"""
        self.bus.write_byte_data(self.address, 0x00, 0x01)
        
        count = 0
        while (self.bus.read_byte_data(self.address, 0x14) & 0x01) == 0:
            time.sleep(0.01)
            count += 1
            if count > 100: return -1
            
        data = self.bus.read_i2c_block_data(self.address, 0x14, 12)
        dist = (data[10] << 8) | data[11]
        
        self.bus.write_byte_data(self.address, 0x0B, 0x01)
        
        return dist

# =============================================================================
# 配置区域
# =============================================================================
SCREEN_WIDTH = 864
SCREEN_HEIGHT = 640

DEG_PER_PIX = 77.0 / SCREEN_WIDTH
Kp_PAN = 0.4
Kp_TILT = 0.4
DEAD_ZONE_X = 10
DEAD_ZONE_Y = 10

SERVO_MIN, SERVO_MAX = -90, 90

BUZZER_PIN = 25
DELAY_THRESHOLD = 0.8

# =============================================================================
# 硬件初始化
# =============================================================================
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUZZER_PIN, GPIO.OUT)
buzzer_active = threading.Event()

servo_tilt = HardwarePWM(pwm_channel=1, hz=50, chip=0)
servo_pan = HardwarePWM(pwm_channel=0, hz=50, chip=0)
servo_tilt.start(12.5)
servo_pan.start(7.5)

servo_pan_angle = 0.0
servo_tilt_angle = 90.0

picam2 = Picamera2()
config = picam2.create_preview_configuration(main={
    "size": (SCREEN_WIDTH, SCREEN_HEIGHT), 
    "format": "RGB888"
})
picam2.configure(config)
picam2.start()

model = YOLO("/home/pi/projects/yolo26/model_folder/ncnn_format_model/640_imgsz_ncnn_model/0207_quadcopter_yolo26_ncnn_model", task='detect')

# 初始化 VL53L0X 传感器
try:
    distance_sensor = VL53L0X_Lite()
    print("VL53L0X 测距传感器初始化成功")
except Exception as e:
    print(f"VL53L0X 初始化失败: {e}")
    distance_sensor = None

# =============================================================================
# 功能函数
# =============================================================================
def set_servo_angle(pwm_obj, angle):
    angle = max(SERVO_MIN, min(SERVO_MAX, angle))
    duty = (angle + 90) * (10 / 180) + 2.5
    pwm_obj.change_duty_cycle(duty)

def blink_handler():
    while True:
        buzzer_active.wait()
        GPIO.output(BUZZER_PIN, GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(BUZZER_PIN, GPIO.LOW)
        time.sleep(0.1)

threading.Thread(target=blink_handler, daemon=True).start()

# =============================================================================
# 主循环
# =============================================================================
first_detected_time = None
frame_count = 0
total_inference_time = 0.0

print("系统就绪: YOLO + 舵机追踪 + 距离检测 + 延迟蜂鸣器")
print("按 Ctrl+C 退出并查看性能报告\n")

try:
    while True:
        start_time = time.time()
        frame = picam2.capture_array()
        results = model(frame, imgsz=640, conf=0.3, verbose=False, stream=True)

        current_frame_valid = False
        target_x, target_y = None, None
        confidence = 0.0

        # 获取当前距离（如果有传感器）
        current_distance = None
        if distance_sensor is not None:
            try:
                dist = distance_sensor.get_distance()
                if dist > 20 and dist < 2000:
                    current_distance = dist
            except:
                pass

        # 解析检测结果
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                w, h = x2 - x1, y2 - y1
                confidence = box.conf[0].item()

                if w >= (SCREEN_WIDTH * 0.7) or h >= (SCREEN_HEIGHT * 0.7):
                    continue

                current_frame_valid = True
                target_x = (x1 + x2) / 2
                target_y = (y1 + y2) / 2
                break

        # 舵机追踪逻辑
        if current_frame_valid:
            error_x = target_x - (SCREEN_WIDTH / 2)
            error_y = target_y - (SCREEN_HEIGHT / 2)

            if abs(error_x) > DEAD_ZONE_X:
                servo_pan_angle -= (error_x * DEG_PER_PIX) * Kp_PAN
                servo_pan_angle = max(SERVO_MIN, min(SERVO_MAX, servo_pan_angle))
                set_servo_angle(servo_pan, servo_pan_angle)

            if abs(error_y) > DEAD_ZONE_Y:
                servo_tilt_angle += (error_y * DEG_PER_PIX) * Kp_TILT
                servo_tilt_angle = max(SERVO_MIN, min(SERVO_MAX, servo_tilt_angle))
                set_servo_angle(servo_tilt, servo_tilt_angle)

        # 蜂鸣器延迟告警逻辑
        if current_frame_valid:
            if first_detected_time is None:
                first_detected_time = time.time()

            duration = time.time() - first_detected_time
            if duration >= DELAY_THRESHOLD:
                if not buzzer_active.is_set():
                    buzzer_active.set()
        else:
            first_detected_time = None
            if buzzer_active.is_set():
                buzzer_active.clear()

        # 终端打印信息（每30帧打印一次）
        frame_count += 1
        total_inference_time += (time.time() - start_time)
        
        if frame_count % 30 == 0:
            print(f"\n{'='*50}")
            print(f"Frame: {frame_count}")
            if current_frame_valid:
                print(f"  Confidence: {confidence*100:.1f}%")
                print(f"  Target Pos: ({int(target_x)}, {int(target_y)})")
                print(f"  Pan Angle: {servo_pan_angle:.1f}°")
                print(f"  Tilt Angle: {servo_tilt_angle:.1f}°")
            else:
                print(f"  Confidence: N/A (No target)")
            
            if current_distance is not None:
                print(f"  Distance: {current_distance} mm ({current_distance/1000:.2f} m)")
            else:
                print(f"  Distance: N/A (Sensor error)")
            
            avg_fps = frame_count / total_inference_time
            print(f"  FPS: {avg_fps:.1f}")
            print(f"{'='*50}")

except KeyboardInterrupt:
    print("\n\n用户停止程序...")

finally:
    # 性能报告
    if frame_count > 0:
        avg_fps = frame_count / total_inference_time
        avg_inference_time = total_inference_time / frame_count
        print("\n" + "="*50)
        print("🚀 性能分析报告")
        print("="*50)
        print(f"总帧数: {frame_count}")
        print(f"总运行时间: {total_inference_time:.2f}秒")
        print(f"平均帧率: {avg_fps:.2f}帧/秒")
        print(f"平均推理时间: {avg_inference_time*1000:.2f}毫秒/帧")
        print("="*50)

    print("\n正在释放资源...")
    buzzer_active.clear()
    picam2.stop()
    set_servo_angle(servo_tilt, 90)
    set_servo_angle(servo_pan, 0)
    time.sleep(1.5)
    servo_pan.stop()
    servo_tilt.stop()
    GPIO.cleanup()
    print("资源已释放")
