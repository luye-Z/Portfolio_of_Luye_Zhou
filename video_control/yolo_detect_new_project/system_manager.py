import cv2
from yolo_predict import YOLODetector
from core_hardware_driver.buzzer_driver import BuzzerController
from core_hardware_driver.vl53l0x_drive_threat import VL53L0X_Threaded
from core_hardware_driver.oled_driver import OLEDDriver
from core_hardware_driver.pwm_servos_control import ServoController
from core_hardware_driver.rgb_led_control import LEDController
from core_hardware_driver.mpu6050_driver import MPU6050driver
from core_hardware_driver.button_driver import ButtonDriver
from core_algorithm.smart_control_algorithm import SmartControlAlgorithm
from core_algorithm.PID_controller import PIDController
import time
import threading
from queue import Queue


class SystemManager:
    """系统管理器，整合所有硬件驱动"""
    
    def __init__(self):
        MODEL_PATH = "/home/pi/projects/yolo26/model_folder/ncnn_format_model/640_imgsz_ncnn_model/0207_quadcopter_yolo26_ncnn_model"
        self.buzzer = BuzzerController()
        self.oled = OLEDDriver()
        self.laser_sensor = VL53L0X_Threaded()
        self.detector = YOLODetector(MODEL_PATH)
        self.servo_controller = ServoController()
        self.rgb_led = LEDController(brightness=0.01)
        self.smart_control_algorithm = SmartControlAlgorithm()# 初始化智能超前预估控制算法
        self.pid_controller = PIDController()
        
        # 初始化按键驱动,并且直接注册了三个按键触发函数
        self.button_driver = ButtonDriver(
            pin=23,
            short_cb=self.action_short_press,
            long_cb=self.action_long_press,
            double_cb=self.action_double_click
            )
        
        # 这些模式中，第一个也就是索引号是0是菜单模式，剩下的是运行模式
        self.program_mode_storage = ("program menu",
                                     "yolo detection\nvc show",
                                     "yolo detection\nno image",
                                     "yolo detection\nno buzzer",
                                     "yolo detection\nno image no buzzer",
                                     "draw_record_chart",
                                     "feedforward_control\ntest",
                                     "draw_record_chart\nfeedback_control")
        self.menu_select_idx = 1
        self.current_program_mode = self.program_mode_storage[0]
        
        # ============ OLED 性能优化部分 ============
        # OLED ��新队列，用于线程间通信
        self.oled_update_queue = Queue(maxsize=1)
        
        # 记录最后一次 OLED 更新时间和内容
        self.last_oled_update_time = 0
        self.last_oled_display_text = None
        
        # OLED 更新最小间隔（秒），限制更新频率为 2Hz（500ms）
        self.OLED_UPDATE_MIN_INTERVAL = 0.5
        
        # 标志位：是否需要立即更新 OLED（用于按键事件）
        self.force_oled_update = False
        
        # 启动 OLED 更新线程
        self.oled_thread_running = True
        self.oled_thread = threading.Thread(target=self._oled_update_worker, daemon=True)
        self.oled_thread.start()
        
        # self.mpu6050 = MPU6050driver()
        # self.mpu6050.calibrate()
        
    def __enter__(self):
        # 统一进入，如果有初始化顺序要求，可以在这里控制
        # 入口程序
        self.detector.start()  # 启动树莓派相机
        self.laser_sensor.start()  # 启动测距线程
        # self.mpu6050.start_reading()  # 启动线程读取数据
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # 统一出口，按顺序关闭设备
        
        # 停止 OLED 线程
        self.oled_thread_running = False
        time.sleep(0.1)  # 等待线程退出
        
        # 短暂延迟，确保 OLED 显示完成
        time.sleep(0.5)
        
        # 清理资源
        
        # 确保蜂鸣器停止报警，然后再清理BUZZER资源
        self.buzzer.stop_alarm()
        self.buzzer.cleanup()
        
        # self.oled.cleanup()
        self.laser_sensor.cleanup()
        self.detector.cleanup()
        self.servo_controller.cleanup()
        
        # 确保 LED 熄灭,然后再清理RGB资源
        self.rgb_led.off()
        self.rgb_led.cleanup()
        
        self.button_driver.cleanup()
        # self.mpu6050.cleanup()
        print("[System] 所有资源已安全释放")
    
    def _oled_update_worker(self):
        """
        OLED 更新工作线程（优化版）
        在独立线程中处理 OLED I2C 通信，不阻塞主程序
        进一步优化：
        - 增加线程睡眠时间，降低 CPU 占用
        - 更严格的更新条件判断
        """
        while self.oled_thread_running:
            try:
                # 非阻塞获取队列中的数据（超时 0.1秒）
                try:
                    display_text = self.oled_update_queue.get_nowait()
                except:
                    # 没有新数据，休眠更长时间，降低CPU占用
                    time.sleep(0.1)
                    continue
                
                current_time = time.time()
                time_elapsed = current_time - self.last_oled_update_time
                
                # 更严格的更新条件：
                # 只在以下情况更新 OLED
                # 1. force_oled_update=True：按键事件，立即更新
                # 2. 距离上次更新超过 OLED_UPDATE_MIN_INTERVAL 且内容改变
                should_update = False
                
                if self.force_oled_update:
                    should_update = True
                elif (time_elapsed >= self.OLED_UPDATE_MIN_INTERVAL and 
                      display_text != self.last_oled_display_text):
                    should_update = True
                
                if should_update:
                    # 执行 I2C 通信（这个操作比较慢，50-200ms）
                    self.oled.show_text(display_text, size=12)
                    
                    # 更新时间戳和内容记录
                    self.last_oled_update_time = current_time
                    self.last_oled_display_text = display_text
                    self.force_oled_update = False  # 重置强制更新标志
                    
            except Exception as e:
                # 捕获所有异常，防止线程崩溃
                time.sleep(0.1)
                continue
    
    def program_mode_manager_oled_show(self, force_update=False):
        """
        非阻塞式 OLED 更新函数（优化版）
        
        :param force_update: 是否立即更新（用于按键事件）
        
        优化点：
        - 先判断内容是否改变，避免不必要的队列操作
        - 减少 CPU 开销
        """
        
        # 1. 生成显示文本
        if self.current_program_mode == self.program_mode_storage[0]:
            selected_name = self.program_mode_storage[self.menu_select_idx]
            display_text = f"--- MENU ---\n> {selected_name}"
        elif self.current_program_mode == self.program_mode_storage[1]:
            display_text = "RUNNING:\nDetection + CV"
        elif self.current_program_mode == self.program_mode_storage[2]:
            display_text = "RUNNING:\nHeadless Mode"
        elif self.current_program_mode == self.program_mode_storage[3]:
            display_text = "RUNNING:\nDetect No Buzzer"
        elif self.current_program_mode == self.program_mode_storage[4]:
            display_text = "RUNNING:\nHeadless No Buzzer"
        elif self.current_program_mode == self.program_mode_storage[5]:
            display_text = "RUNNING:\nDraw charts"   
        elif self.current_program_mode == self.program_mode_storage[6]:
            display_text = "RUNNING:\nFeedforward Control Test"
        elif self.current_program_mode == self.program_mode_storage[7]:
            display_text = "RUNNING:\nFeedback Control Test"
        
        else:
            return  # 异常模式，不更新
        
        # 2. 检查是否真的需要更新（内容相同且非强制更新则跳过）
        if not force_update and display_text == self.last_oled_display_text:
            return  # 内容没变，直接跳过，不放入队列
        
        # 3. 按键事件时设置强制更新标志
        if force_update:
            self.force_oled_update = True
        
        # 4. 将更新请求放入队列（非阻塞）
        try:
            self.oled_update_queue.put_nowait(display_text)
        except:
            # 队列满时舍弃旧请求，放入新请求
            try:
                self.oled_update_queue.get_nowait()
                self.oled_update_queue.put_nowait(display_text)
            except:
                pass
    
    # =====================按键相关函数==============================
    def action_short_press(self):
        """短按处理"""
        print("【短按】")
        if self.get_program_mode() == self.program_mode_storage[0]:
            # 如果当前模式是菜单模式
            self.menu_select_idx += 1
            if self.menu_select_idx >= len(self.program_mode_storage):
                self.menu_select_idx = 1
            
            # 按键事件：强制立即更新 OLED
            self.program_mode_manager_oled_show(force_update=True)
    
    def action_long_press(self):
        """长按处理"""
        print("【长按】->进入系统设置")
        if self.get_program_mode() != self.program_mode_storage[0]:
            # 当前模式不是菜单模式，是运行模式之一
            self.program_mode_set(0)
            self.menu_select_idx = 1
            
            # 按键事件：强制立即更新 OLED
            self.program_mode_manager_oled_show(force_update=True)
                    
            #还需要清理一些GPIO外设，蜂鸣器，RGB灯，等等，要不然可能会出现模式切换，蜂鸣器一直卡在鸣叫的状态里面
            self.rgb_led.off() # 关闭RGB灯
            self.buzzer.stop_alarm() # 关闭蜂鸣器
            self.servo_controller.reset() # 重置舵机角度

            self.pid_controller.reset_control_parameters() # 重置PID控制器参数
            
    def action_double_click(self):
        """双击处理"""
        print("【双击】->")
        if self.get_program_mode() == self.program_mode_storage[0]:
            # 当前模式是菜单模式
            self.program_mode_set(self.menu_select_idx)
            
            # 按键事件：强制立即更新 OLED
            self.program_mode_manager_oled_show(force_update=True)
    
    # =====================获取/设置函数==============================
    def get_program_mode(self):
        """获取当前程��模式"""
        return self.current_program_mode
    
    def program_mode_set(self, mode_index):
        """
        设置当前程序模式
        
        :param mode_index: 模式索引
            - 0: 菜单模式
            - 1: YOLO 检测 + 显示模式
            - 2: YOLO 检测 + 无显示模式
        """
        self.current_program_mode = self.program_mode_storage[mode_index]


if __name__ == "__main__":
    # 启动线程读取数据
    with SystemManager() as sys:
        
        # 初始化显示
        sys.program_mode_manager_oled_show()
        
        # 主程序继续执行其他任务
        while True:
            print(f"当前模式: {sys.get_program_mode()}")
            time.sleep(2)  # 示例的主程序工作