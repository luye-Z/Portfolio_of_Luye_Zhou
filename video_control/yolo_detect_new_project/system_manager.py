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
        #这些模式中，第一个也就是索引号是0是菜单模式，剩下的是运行模式
        self.program_mode_storage = ("program menu","yolo detection\nvc show","yolo detection\nno image")  # 初始化为检测模式
        self.menu_select_idx = 1  #代表着当前菜单是第一页，也就是OLED显示yolo_detection_vc_show
                                    #一个比较巧妙的设计是，这里的menu_select_idx = 1 和program_mode_storage[1] 是对应的
        self.current_program_mode = self.program_mode_storage[0]                     
        
        # self.mpu6050 = MPU6050driver()
        #mpu6050比较特殊，他需要一点时间去校准传感器
        # self.mpu6050.calibrate()
    def __enter__(self):
        # 统一进入，如果有初始化顺序要求，可以在这里控制
        # 入口程序
        self.detector.start()  #启动树莓派相机
        self.laser_sensor.start()  # 启动测距线程
        # self.mpu6050.start_reading()  # 启动线程读取数据
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # 统一出口，按顺序关闭设备
        
        # 在 OLED 屏幕上显示退出信息
        # self.oled.text("SYSTEM\\nSHUTTING DOWN...\\nBYE!")
        
        # 短暂延迟，确保 OLED 显示完成
        import time
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
        
    def program_mode_manager_oled_show(self):
        """根据当前状态刷新 OLED 屏幕显示内容"""
        
        # 1. 如果处于“菜单模式”
        if self.current_program_mode == self.program_mode_storage[0]:
            # 获取当前选中的模式名称
            selected_name = self.program_mode_storage[self.menu_select_idx]
            
            # 构建显示文本：第一行是标题，第二行是带光标的选项
            # \n 代表换行
            display_text = f"--- MENU ---\n> {selected_name}"
            # selected_name = selected_name.replace("@", "\n")
            self.oled.show_text(display_text, size=12)
            
        # 2. 如果处于“YOLO 显示模式”
        elif self.current_program_mode == self.program_mode_storage[1]:
            self.oled.show_text("RUNNING:\nDetection + CV", size=12)
            
        # 3. 如果处于“YOLO 静默模式”
        elif self.current_program_mode == self.program_mode_storage[2]:
            self.oled.show_text("RUNNING:\nHeadless Mode", size=12)


        #=====================按键相关函数==============================
    def action_short_press(self):
        print("【短按】")
        if self.get_program_mode() == self.program_mode_storage[0] :
            #如果当前模式是菜单模式 
            self.menu_select_idx +=1  # 菜单索引增加1，代表着选择了下一个模式
            if self.menu_select_idx >= len(self.program_mode_storage): # 标签索引越界
                self.menu_select_idx = 1  # 重置索引，回到第一个模式
                
            self.program_mode_manager_oled_show() # 刷新 OLED 显示
                
            # self.oled.show_text("选择模式\\nyolo_detection_vc_show", size=12)
        #执行，如果当前程序模式是program_menu，在OLED屏幕上显示“选择模式yolo_detection_vc_show”
        #再短按一次，在OLED屏幕上显示“选择模式yolo_detection_no_image”，
        #再短按一次，在OLED屏幕上显示“选择模式yolo_detection_vc_show”
        #如此循环
        
        
    def action_long_press(self):
        print("【长按】->进入系统设置")
        if self.get_program_mode() != self.program_mode_storage[0] :#当前模式不是菜单模式，是运行模式之一
            self.program_mode_set(0) #切换到菜单模式
            self.menu_select_idx = 1 # 重置菜单光标到第一个
            
            self.program_mode_manager_oled_show() # 刷新 OLED 显示
            #在OLED屏幕上显示“选择模式yolo_detection_vc_show”
        #如果当前模式是两个运行模式之一，则跳转到菜单模式
        
    def action_double_click(self):
        print("【双击】->")
        if self.get_program_mode() == self.program_mode_storage[0] :#当前模式是菜单模式
            self.program_mode_set(self.menu_select_idx) #切换到OLED屏幕上显示的模式
            
            # 刷新屏幕显示“运行中”的状态
            self.program_mode_manager_oled_show()
        #如果当前模式是菜单模式 ，双击则进入OLED屏幕上显示的模式
#===================================================

    def get_program_mode(self):
        """获取当前程序模式"""
        return self.current_program_mode
    
    
    def program_mode_set(self,mode_index):
        """设置当前程序模式,mode_index为模式索引,0为菜单模式,1为显示模式,2为无图像模式"""
 
        
        #这行代码作为参考self.program_mode_storage = ("program_menu","yolo_detection_vc_show","yolo_detection_no_image")  # 初始化为检测模式
        self.current_program_mode = self.program_mode_storage[mode_index]

if __name__ == "__main__":
    # 启动线程读取数据
    with SystemManager() as sys:
        
        
        sys.program_mode_manager_oled_show()
            
        # 主程序继续执行其他任务
        while True:
            
            
            print(f"当前模式: {sys.get_program_mode()}")
            time.sleep(2)  # 示例的主程序工作
    
    # 主程序继续执行其他任务
        # while True:
        # # 主程序可以执行其他任务
           
        #     print(f"Pitch: {sys.mpu6050.get_mpu6050_angle_pose()[0]:.2f}°, Roll: {sys.mpu6050.get_mpu6050_angle_pose()[1]:.2f}°")
           
        #     time.sleep(0.1)  # 示例的主程序工作
