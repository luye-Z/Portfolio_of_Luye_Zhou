from yolo_predict import YOLODetector
from buzzer_driver import BuzzerController
from vl53l0x_drive_threat import VL53L0X_Threaded
from oled_driver import OLED_Driver


class SystemManager:
    def __init__(self):
        MODEL_PATH = "/home/pi/projects/yolo26/model_folder/ncnn_format_model/640_imgsz_ncnn_model/0207_quadcopter_yolo26_ncnn_model"
        self.buzzer = BuzzerController()
        self.oled = OLED_Driver()
        self.laser_sensor = VL53L0X_Threaded()
        self.detector = YOLODetector(MODEL_PATH)
        
    def __enter__(self):
        # 统一进入，如果有初始化顺序要求，可以在这里控制
        # 入口程序
        self.detector.start()  #启动树莓派相机
        self.laser_sensor.start()  # 启动测距线程
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 统一出口，按顺序关闭设备
        
        self.buzzer.cleanup()
        self.oled.cleanup()
        self.laser_sensor.cleanup()
        self.detector.cleanup()
        print("[System] 所有资源已安全释放")

# # 使用时
# with SystemManager() as sys:
#     while True:
#         results = sys.detector.model.detect(sys.camera.read())
#         sys.oled.draw_text(...)