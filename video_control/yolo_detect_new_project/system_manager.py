import cv2
from yolo_predict import YOLODetector
from buzzer_driver import BuzzerController
from vl53l0x_drive_threat import VL53L0X_Threaded
from oled_driver import OLEDDriver
from pwm_servos_control import ServoController
from rgb_led_control import LEDController
from mpu6050_driver import MPU6050driver
from button_driver import ButtonDriver

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
        
        # 初始化按键驱动,并且直接注册了三个按键触发函数
        self.button_driver = ButtonDriver(
            pin=23,
            short_cb=self.action_short_press,
            long_cb=self.action_long_press,
            double_cb=self.action_double_click
            )
        
        # 这些模式中，第一个也就是索引号是0是菜单模式，剩下的是运行模式
        self.program_mode_storage = ("program menu","yolo detection\nvc show","yolo detection\nno image")
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
        self.buzzer.cleanup()
        # self.oled.cleanup()
        self.laser_sensor.cleanup()
        self.detector.cleanup()
        self.servo_controller.cleanup()
        self.rgb_led.cleanup()
        self.button_driver.cleanup()
        # self.mpu6050.cleanup()
        print("[System] 所有资源已安全释放")
    
    def _oled_update_worker(self):
        """
        OLED 更新工作线程
        在独立线程中处理 OLED I2C 通信，不阻塞主程序
        采用智能节流机制：
        1. 非按键事件：限制更新频率为 2Hz（500ms 间隔）
        2. 按键事件：立即更新（force_oled_update=True）
        """
        while self.oled_thread_running:
            try:
                # 非阻塞获取队列中的数据（超时 100ms）
                display_text = self.oled_update_queue.get(timeout=0.1)
                
                current_time = time.time()
                time_elapsed = current_time - self.last_oled_update_time
                
                # 判断是否需要更新：
                # 1. force_oled_update=True：按键事件，立即更新
                # 2. 距离上次更新超过 OLED_UPDATE_MIN_INTERVAL
                # 3. 显示内容改变
                
                should_update = (
                    self.force_oled_update or 
                    time_elapsed >= self.OLED_UPDATE_MIN_INTERVAL or
                    display_text != self.last_oled_display_text
                )
                
                if should_update:
                    # 执行 I2C 通信（这个操作比较慢，50-200ms）
                    self.oled.show_text(display_text, size=12)
                    
                    # 更新时间戳和内容记录
                    self.last_oled_update_time = current_time
                    self.last_oled_display_text = display_text
                    self.force_oled_update = False  # 重置强制更新标志
                    
            except:
                # 队列超时（没有新数据），继续等待
                pass
    
    def program_mode_manager_oled_show(self, force_update=False):
        """
        非阻塞式 OLED 更新函数
        
        :param force_update: 是否立即更新（用于按键事件）
        
        说明：
        - 正常情况下：将更新请求放入队列，由后台线程处理，不阻塞主程序
        - 按键事件时：设置 force_update=True，立即更新 OLED 以获得快速响应
        """
        
        # 1. 如果处于"菜单模式"
        if self.current_program_mode == self.program_mode_storage[0]:
            selected_name = self.program_mode_storage[self.menu_select_idx]
            display_text = f"--- MENU ---\n> {selected_name}"
        
        # 2. 如果处于"YOLO 显示模式"
        elif self.current_program_mode == self.program_mode_storage[1]:
            display_text = "RUNNING:\nDetection + CV"
        
        # 3. 如果处于"YOLO 静默模式"
        elif self.current_program_mode == self.program_mode_storage[2]:
            display_text = "RUNNING:\nHeadless Mode"
        else:
            return  # 异常模式，不更新
        
        # 按键事件时设置强制更新标志
        if force_update:
            self.force_oled_update = True
        
        # 将更新请求放入队列（非阻塞）
        try:
            # maxsize=1 意味着队列只保存最新的一条请求
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