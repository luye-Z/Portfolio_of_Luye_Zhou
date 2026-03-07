class PIDController:
    def __init__(self, kp_pan = 0.1, kp_tilt = 0.1, kd_pan = 0.05, kd_tilt = 0.05   ):
        
        self.kp_pan = kp_pan
        self.kp_tilt = kp_tilt
        self.kd_pan = kd_pan
        self.kd_tilt = kd_tilt
        self.dead_zone = 10  # 死区（像素）

        # 状态记录

        self.current_pan = 0.0
        self.current_tilt = 90.0  # 初始向上看
        
        # PD 控制需要上一次误差
        self.last_error_x = 0.0
        self.last_error_y = 0.0
        
        #像素角分辨率 (Pixel Angular Resolution)
        #77°/864像素(screen_width)
        self.DEG_PER_PIX = 77.0 / 864  # 根据你的 SCREEN_WIDTH 自动适配
        
        self.SCREEN_WIDTH = 864
        self.SCREEN_HEIGHT = 640
                
    def pid_control_calculate(self, target_x, target_y):

        """

        PD算法核心：根据YOLO检测到的目标位置计算更新舵机控制角度

        """

        # 1. 计算误差 (Error)

        error_x = target_x - (self.SCREEN_WIDTH / 2)
        error_y = target_y - (self.SCREEN_HEIGHT / 2)
        
        # 计算误差变化率（微分项）
        error_diff_x = error_x - self.last_error_x
        error_diff_y = error_y - self.last_error_y



        # 2. 水平追踪 (Pan)

        if abs(error_x) > self.dead_zone:

            # PD 控制公式：delta = kp * error + kd * (error - last_error)
            # delta_pan = (error_x * self.DEG_PER_PIX) * self.kp_pan + (error_diff_x * self.DEG_PER_PIX) * self.kd_pan
            delta_pan = self.DEG_PER_PIX*(self.kp_pan * error_x + self.kd_pan * error_diff_x)   
            self.current_pan -= delta_pan  # 镜像调整

            # self._set_angle(self.servo_pan, self.current_pan)

        # 3. 垂直追踪 (Tilt)

        if abs(error_y) > self.dead_zone:

            #delta_tilt = (error_y * self.DEG_PER_PIX) * self.kp_tilt + (error_diff_y * self.DEG_PER_PIX) * self.kd_tilt
            # 垂直方向需要反转，所以用减法
            delta_tilt = self.DEG_PER_PIX*(self.kp_tilt * error_y + self.kd_tilt * error_diff_y)
            self.current_tilt += delta_tilt

            # self._set_angle(self.servo_tilt, self.current_tilt)
        
        # 4. 更新上一次误差
        self.last_error_x = error_x
        self.last_error_y = error_y

    def get_PID_controller_output(self):
        # 返回当前的 pan 和 tilt 角度,直接给这个角度输入给舵机
        return self.current_pan, self.current_tilt
    
