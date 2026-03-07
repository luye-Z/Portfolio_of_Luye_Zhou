import RPi.GPIO as GPIO
import threading
import time


class BuzzerController:
    def __init__(self, pin=25):
        """
        初始化蜂鸣器控制器
        :param pin: 蜂鸣器连接的GPIO引脚 (BCM编号)
        """
        self.buzzer_pin = pin
        self._active_event = threading.Event()  # 用于控制报警启停
        self._stop_event = threading.Event()   # 用于彻底销毁线程
        
        # GPIO 初始化
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.buzzer_pin, GPIO.OUT)
        GPIO.output(self.buzzer_pin, 0)
        
        # 启动后台守护线程
        self._thread = threading.Thread(target=self._handler, daemon=True)
        self._thread.start()
    
    def _handler(self):
        """内部线程函数：处理蜂鸣逻辑"""
        while not self._stop_event.is_set():
            # 等待激活信号 (wait 会挂起线程，不占CPU)
            if self._active_event.wait(timeout=0.5):  # 这行执行成功了，进入下一段，否则继续等待
                # 产生"滴滴"声
                while self._active_event.is_set() and not self._stop_event.is_set():
                    GPIO.output(self.buzzer_pin, 1)
                    time.sleep(0.1)
                    GPIO.output(self.buzzer_pin, 0)
                    time.sleep(0.1)
    
    def start_alarm(self):
        """开始报警（滴滴声）"""
        if not self._active_event.is_set():
            self._active_event.set()
            print("[Buzzer] Alarm started.")
    
    def stop_alarm(self):
        """停止报警"""
        if self._active_event.is_set():
            self._active_event.clear()
            GPIO.output(self.buzzer_pin, 0)  # 使用 0 而不是 GPIO.LOW
            print("[Buzzer] Alarm stopped.")
    
    def cleanup(self):
        """彻底停止并释放资源"""
        self._stop_event.set()  # 停止循环
        self._active_event.set()  # 唤醒可能在wait中的线程
        self.stop_alarm()
        # 注意：通常 GPIO.cleanup() 由主程序统一调用
        # 但可以在这里确保当前引脚关闭
        GPIO.output(self.buzzer_pin, 0)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
        return False
    
    def __del__(self):
        self.cleanup()


# =============================================================================
# 单元测试 (使用方法演示)
# =============================================================================
if __name__ == "__main__":
    with BuzzerController() as buzzer:
        
        while True:
            cmd = input("输入 s(开始) / e(停止) / q(退出): ").lower()
            if cmd == 's':
                buzzer.start_alarm()
            elif cmd == 'e':
                buzzer.stop_alarm()
            elif cmd == 'q':
                break
