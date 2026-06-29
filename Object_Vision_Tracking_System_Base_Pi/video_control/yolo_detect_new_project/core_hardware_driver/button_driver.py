import RPi.GPIO as GPIO
import time
from threading import Timer

class ButtonDriver:
    def __init__(self, pin=23, short_cb=None, long_cb=None, double_cb=None, 
                 double_click_window=0.6, long_press_threshold=1.5, bouncetime=30):
        """
        :param pin: GPIO 引脚号 (BCM 模式)
        :param double_click_window: 【关键调参】双击等待窗口（秒）。
                                   手指松开后，等待第二次按下的时间。越小反应越快，但双击难度越大。
        :param long_press_threshold: 长按判定阈值（秒）。
        :param bouncetime: 硬件消抖时间（毫秒）。
        """
        self.pin = pin
        self.short_cb = short_cb
        self.long_cb = long_cb
        self.double_cb = double_cb
        
        # 调试参数
        self.double_click_window = double_click_window
        self.long_press_threshold = long_press_threshold
        
        # 内部状态管理
        self.last_press_time = 0
        self.timer = None 
        self.is_double_click_pending = False

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        
        # 使用传入的 bouncetime 参数
        GPIO.add_event_detect(self.pin, GPIO.BOTH, callback=self._handle_event, bouncetime=bouncetime)

    def _handle_event(self, channel):
        current_time = time.time()
        is_pressed = GPIO.input(self.pin)

        if is_pressed:
            # --- 按下动作 ---
            if self.timer and self.timer.is_alive():
                self.timer.cancel()
                self.timer = None
                self.is_double_click_pending = True
                self._safe_call(self.double_cb)
            else:
                self.is_double_click_pending = False
                self.last_press_time = current_time
        else:
            # --- 松开动作 ---
            if self.is_double_click_pending:
                return

            press_duration = current_time - self.last_press_time

            if press_duration >= self.long_press_threshold:
                self._safe_call(self.long_cb)
            else:
                if self.timer:
                    self.timer.cancel()
                # 使用定义的变量 double_click_window
                self.timer = Timer(self.double_click_window, self._trigger_short)
                self.timer.start()

    def _trigger_short(self):
        self._safe_call(self.short_cb)

    def _safe_call(self, callback):
        if callback:
            try:
                callback()
            except Exception as e:
                print(f"回调执行出错: {e}")
                
    def cleanup(self):
        if self.timer:
            self.timer.cancel()
        try:
            GPIO.remove_event_detect(self.pin)
        except:
            pass
        print(f"按键引脚 {self.pin} 已释放")

# ==========================================
# 使用示例
# ==========================================

def action_short_press():
    print("【短按】-> 切换灯光")

def action_long_press():
    print("【长按】-> 进入设置")

def action_double_click():
    print("【双击】-> 播放/暂停")

if __name__ == "__main__":
    try:
        btn = ButtonDriver(
            pin=23,
            short_cb=action_short_press,
            long_cb=action_long_press,
            double_cb=action_double_click
        )
        
        print("驱动就绪。操作逻辑：")
        print("- 短按：松开后 0.3s 触发")
        print("- 双击：第二次按下时立即触发")
        print("- 长按：按住 1s 后松开触发")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n正在退出...")
    finally:
        GPIO.cleanup()