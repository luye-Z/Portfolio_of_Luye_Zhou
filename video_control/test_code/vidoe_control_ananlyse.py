import cv2
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
        self.bus.write_byte_data(self.address, 0x88, 0x00)
        self.bus.write_byte_data(self.address, 0x80, 0x01)
        self.bus.write_byte_data(self.address, 0xFF, 0x01)
        self.bus.write_byte_data(self.address, 0x00, 0x00)
        self.bus.write_byte_data(self.address, 0x91, 0x3c)
        self.bus.write_byte_data(self.address, 0x00, 0x01)
        self.bus.write_byte_data(self.address, 0xFF, 0x00)
        self.bus.write_byte_data(self.address, 0x80, 0x00)

    def get_distance(self):
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
# 1. Hardware Configuration
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

picam2 = Picamera2()
config = picam2.create_preview_configuration(main={
    "size": (SCREEN_WIDTH, SCREEN_HEIGHT), 
    "format": "RGB888"
})
picam2.configure(config)
picam2.start()

model = YOLO("/home/pi/projects/yolo26/model_folder/ncnn_format_model/640_imgsz_ncnn_model/0207_quadcopter_yolo26_ncnn_model", task='detect')

try:
    distance_sensor = VL53L0X_Lite()
    print("VL53L0X 测距传感器初始化成功")
except Exception as e:
    print(f"VL53L0X 初始化失败: {e}")
    distance_sensor = None

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUZZER_PIN, GPIO.OUT)
buzzer_active = threading.Event()

servo_tilt = HardwarePWM(pwm_channel=1, hz=50, chip=0)
servo_pan = HardwarePWM(pwm_channel=0, hz=50, chip=0)
servo_tilt.start(12.5)
servo_pan.start(7.5)

servo_pan_angle = 0.0
servo_tilt_angle = 90.0

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
# 2. Performance Metrics Initialization
# =============================================================================
frame_counts = 0
total_inference_time = 0
total_preprocess_time = 0
total_postprocess_time = 0
session_start_time = time.time()
first_detected_time = None

print("系统就绪: YOLO + 舵机追踪 + 距离检测 + 延迟蜂鸣器")
print("Press 'q' to quit and view Performance Report.")

try:
    while True:
        # Capture frame
        frame = picam2.capture_array()
        
        # Inference
        results = model(frame, imgsz=640, conf=0.3, verbose=False)

        # Accumulate timing from Ultralytics internal dictionary (ms)
        speed = results[0].speed
        total_preprocess_time += speed['preprocess']
        total_inference_time += speed['inference']
        total_postprocess_time += speed['postprocess']
        frame_counts += 1

        # Calculate Real-time FPS for display
        latency_ms = sum(speed.values())
        rt_fps = 1000 / latency_ms if latency_ms > 0 else 0
        
        # Process detection results
        annotated_frame = results[0].plot()
        current_frame_valid = False
        target_x, target_y = None, None
        confidence = 0.0

        # Get distance measurement
        current_distance = None
        if distance_sensor is not None:
            try:
                dist = distance_sensor.get_distance()
                if dist > 20 and dist < 2000:
                    current_distance = dist
            except:
                pass

        # Find first valid detection
        for box in results[0].boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            w, h = x2 - x1, y2 - y1
            confidence = box.conf[0].item()

            if w >= (SCREEN_WIDTH * 0.7) or h >= (SCREEN_HEIGHT * 0.7):
                continue

            current_frame_valid = True
            target_x = (x1 + x2) / 2
            target_y = (y1 + y2) / 2

            # Draw custom annotations
            cv2.rectangle(annotated_frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
            cv2.circle(annotated_frame, (int(target_x), int(target_y)), 5, (0, 0, 255), -1)
            cv2.putText(annotated_frame, f"Conf: {confidence*100:.1f}%", 
                        (int(x1), int(y1)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

            if current_distance is not None:
                dist_text = f"Dist: {current_distance}mm"
                cv2.putText(annotated_frame, dist_text, 
                            (int(x1), int(y2)+20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)

            break

        # Servo tracking logic
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

        # Buzzer delay alert logic
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

        # Display rendering
        display_frame = cv2.resize(annotated_frame, (820, 616))
        cv_dz_x = int(DEAD_ZONE_X * (820 / SCREEN_WIDTH))
        cv_dz_y = int(DEAD_ZONE_Y * (616 / SCREEN_HEIGHT))
        cv2.rectangle(display_frame, 
                      (410 - cv_dz_x, 308 - cv_dz_y), 
                      (410 + cv_dz_x, 308 + cv_dz_y), (255, 255, 0), 1)

        # Display distance info
        if current_distance is not None:
            cv2.putText(display_frame, f"Target Dist: {current_distance}mm", 
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

        # Display real-time FPS
        cv2.putText(display_frame, f"FPS: {rt_fps:.1f}", (30, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)

        cv2.imshow("Pi5 Tracking System", display_frame)

        if cv2.waitKey(1) == ord("q"):
            break

finally:
    # =============================================================================
    # 3. Performance Analysis Log
    # =============================================================================
    session_end_time = time.time()
    total_duration = session_end_time - session_start_time
    
    if frame_counts > 0:
        avg_pre = total_preprocess_time / frame_counts
        avg_inf = total_inference_time / frame_counts
        avg_post = total_postprocess_time / frame_counts
        avg_total_latency = avg_pre + avg_inf + avg_post
        avg_fps = frame_counts / total_duration

        print("\n" + "="*40)
        print("🚀 YOLO NCNN PERFORMANCE REPORT")
        print("="*40)
        print(f"Total Frames Processed:  {frame_counts}")
        print(f"Total Session Duration: {total_duration:.2f} s")
        print("-" * 40)
        print(f"Avg Preprocess:         {avg_pre:.2f} ms")
        print(f"Avg Inference:          {avg_inf:.2f} ms")
        print(f"Avg Postprocess:        {avg_post:.2f} ms")
        print(f"Avg Total Latency:      {avg_total_latency:.2f} ms")
        print("-" * 40)
        print(f"AVG PIPELINE FPS:       {avg_fps:.2f}")
        
        # Bottleneck Analysis
        if avg_inf > (avg_pre + avg_post):
            bottleneck = "Neural Network Inference (CPU bound)"
        else:
            bottleneck = "Image I/O or Rendering"
        print(f"Primary Bottleneck:     {bottleneck}")
        print("="*40)

    print("\n正在释放资源...")
    buzzer_active.clear()
    picam2.stop()
    set_servo_angle(servo_tilt, 90)
    set_servo_angle(servo_pan, 0)
    time.sleep(1.5)
    servo_pan.stop()
    servo_tilt.stop()
    cv2.destroyAllWindows()
    GPIO.cleanup()