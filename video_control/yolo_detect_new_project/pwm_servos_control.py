import time

from rpi_hardware_pwm import HardwarePWM



class ServoController:

    def __init__(self, pan_chan=0, tilt_chan=1, chip_id=0, kp_pan=0.2, kp_tilt=0.2):

        """

        集成了 P 控制算法的舵机控制器

        :param kp_pan: 水平比例系数（通常 0.1~0.6）

        :param kp_tilt: 垂直比例系数

        """

        # 硬件初始化

        self.servo_pan = HardwarePWM(pwm_channel=pan_chan, hz=50, chip=chip_id)

        self.servo_tilt = HardwarePWM(pwm_channel=tilt_chan, hz=50, chip=chip_id)

        

        # 物理参数

        self.SERVO_MIN, self.SERVO_MAX = -90, 90

        self.DEG_PER_PIX = 77.0 / 864  # 根据你的 SCREEN_WIDTH 自动适配

        

        # P 控制参数

        self.kp_pan = kp_pan

        self.kp_tilt = kp_tilt

        self.dead_zone = 10  # 死区（像素）



        # 状态记录

        self.current_pan = 0.0

        self.current_tilt = 90.0  # 初始向上看

        

        # 启动

        self.servo_pan.start(7.5)

        self.servo_tilt.start(12.5)

        print(f"PID-Ready ServoController: Kp_P={kp_pan}, Kp_T={kp_tilt}")



    def _set_angle(self, pwm_obj, angle):

        """内部映射：角度 -> 占空比"""

        angle = max(self.SERVO_MIN, min(self.SERVO_MAX, angle))

        duty = (angle + 90) * (10 / 180) + 2.5

        pwm_obj.change_duty_cycle(duty)



    def track_target(self, target_x, target_y, screen_w, screen_h):

        """

        P算法核心：根据目标位置更新舵机角度

        """

        # 1. 计算误差 (Error)

        error_x = target_x - (screen_w / 2)

        error_y = target_y - (screen_h / 2)



        # 2. 水平追踪 (Pan)

        if abs(error_x) > self.dead_zone:

            # P 控制公式

            delta_pan = (error_x * self.DEG_PER_PIX) * self.kp_pan

            self.current_pan -= delta_pan  # 镜像调整

            self._set_angle(self.servo_pan, self.current_pan)



        # 3. 垂直追踪 (Tilt)

        if abs(error_y) > self.dead_zone:

            delta_tilt = (error_y * self.DEG_PER_PIX) * self.kp_tilt

            self.current_tilt += delta_tilt 

            self._set_angle(self.servo_tilt, self.current_tilt)



        return self.current_pan, self.current_tilt



    def reset(self):

        """复位"""

        self.current_pan, self.current_tilt = 0, 90

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