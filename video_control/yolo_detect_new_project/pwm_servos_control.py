import time

from rpi_hardware_pwm import HardwarePWM



class ServoController:

    def __init__(self, pan_chan=0, tilt_chan=1, chip_id=0, kp_pan=0.10, kp_tilt=0.10, kd_pan=0.01, kd_tilt=0.01):

        """

        集成了 PD 控制算法的舵机控制器

        :param kp_pan: 水平比例系数（通常 0.1~0.6）
        :param kp_tilt: 垂直比例系数
        :param kd_pan: 水平微分系数（通常 0.05~0.3）
        :param kd_tilt: 垂直微分系数

        """

        # 硬件初始化

        self.servo_pan = HardwarePWM(pwm_channel=pan_chan, hz=50, chip=chip_id)

        self.servo_tilt = HardwarePWM(pwm_channel=tilt_chan, hz=50, chip=chip_id)

        

        # 物理参数

        self.SERVO_MIN, self.SERVO_MAX = -90, 90

        # self.DEG_PER_PIX = 77.0 / 864  # 根据你的 SCREEN_WIDTH 自动适配

        

  

        

        # 启动

        self.servo_pan.start(7.5)

        self.servo_tilt.start(12.5)

        # print(f"PD-Ready ServoController: Kp_P={kp_pan}, Kp_T={kp_tilt}, Kd_P={kd_pan}, Kd_T={kd_tilt}")



    def _set_angle(self, pwm_obj, angle):

        """内部映射：角度 -> 占空比"""

        angle = max(self.SERVO_MIN, min(self.SERVO_MAX, angle))

        duty = (angle + 90) * (10 / 180) + 2.5

        pwm_obj.change_duty_cycle(duty)
    def set_pan_angle(self, angle):

        """设置水平角度"""

        self._set_angle(self.servo_pan, angle)  
        
    def set_tilt_angle(self, angle):

        """设置垂直角度"""

        self._set_angle(self.servo_tilt, angle) 



    def reset(self):

        """复位"""

        self.current_pan, self.current_tilt = 0, 90
        self.last_error_x = 0.0
        self.last_error_y = 0.0

        self._set_angle(self.servo_pan, 0)

        self._set_angle(self.servo_tilt, 90)
        
        



    def stop(self):

        """安全释放"""

        self.reset()

        time.sleep(0.5)

        self.servo_pan.stop()

        self.servo_tilt.stop()

        

    def cleanup(self):

        """清理资源"""

        self.stop()

        

        

    def __enter__(self):

        """上下文管理器入口"""

        return self

    

    def __exit__(self, exc_type, exc_val, exc_tb):

        """上下文管理器出口"""

        self.cleanup()

        return False 
