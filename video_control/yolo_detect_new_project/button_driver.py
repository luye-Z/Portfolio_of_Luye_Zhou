import RPi.GPIO as GPIO
import time
from threading import Timer

class ButtonDriver:
    def __init__(self, pin=23, short_cb=None, long_cb=None, double_cb=None):
        self.pin = pin
        self.short_cb = short_cb
        self.long_cb = long_cb
        self.double_cb = double_cb
        
        # 内部状态管理
        self.last_press_time = 0
        self.last_release_time = 0
        self.timer = None 

        # GPIO 初始化（带警告关闭，更稳健）
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        
        # 绑定硬件中断：无论是按下还是松开，都会触发 _handle_event
        GPIO.add_event_detect(self.pin, GPIO.BOTH, callback=self._handle_event, bouncetime=30)

    def _handle_event(self, channel):
        """核心逻辑：处理按键电平变化"""
        current_time = time.time()
        
        # 读取当前引脚状态 (High为按下, Low为松开)
        is_pressed = GPIO.input(self.pin)

        if is_pressed:
            # --- 按下动作 ---
            self.last_press_time = current_time
            # 如果之前有一个“等待确认是否为双击”的定时器，立即取消它
            if self.timer:
                self.timer.cancel()
        else:
            # --- 松开动作 ---
            press_duration = current_time - self.last_press_time
            
            # 1. 长按判定 (按下超过 1 秒)
            if press_duration >= 1.0:
                self._safe_call(self.long_cb)
            
            # 2. 双击判定 (本次松开距离上次松开小于 0.4 秒)
            elif (current_time - self.last_release_time) < 0.4:
                if self.timer:
                    self.timer.cancel()
                self._safe_call(self.double_cb)
                self.last_release_time = 0 # 成功触发双击，清空计数
            
            # 3. 可能是短按，开启定时器等待 0.3 秒确认
            else:
                self.last_release_time = current_time
                self.timer = Timer(0.3, self._trigger_short)
                self.timer.start()

    def _trigger_short(self):
        """定时器结束，确认是短按"""
        self._safe_call(self.short_cb)

    def _safe_call(self, callback):
        """安全调用回调函数，防止回调出错导致主线程崩溃"""
        if callback:
            try:
                callback()
            except Exception as e:
                print(f"回调执行出错: {e}")
                
    def cleanup(self):
        """释放资源，停止所有后台任务"""
        # 1. 取消正在运行的定时器，防止程序退出后还在后台“闹钟”
        if self.timer:
            self.timer.cancel()
        
        # 2. 移除该引脚的中断监听
        try:
            GPIO.remove_event_detect(self.pin)
        except:
            pass
        
        print(f"按键引脚 {self.pin} 已安全释放")

# ==========================================
# 易读的使用示例
# ==========================================

# 1. 先定义具体的动作函数（简单明了）
def action_short_press():
    print("【短按】-> 执行：切换灯光状态")

def action_long_press():
    print("【长按】-> 执行：进入系统设置")

def action_double_click():
    print("【双击】-> 执行：播放/暂停音乐")

# 2. 主程序运行
if __name__ == "__main__":
    try:
        # 将上面定义的函数名作为参数传入
        btn = ButtonDriver(
            pin=23,
            short_cb=action_short_press,
            long_cb=action_long_press,
            double_cb=action_double_click
        )
        
        print("按键驱动已就绪（引脚23，下拉模式）")
        print("按 Ctrl+C 退出程序...")
        
        while True:
            time.sleep(1) # 主循环保持运行
            
    except KeyboardInterrupt:
        print("\n程序正常退出")
    finally:
        GPIO.cleanup() # 必须清理，释放资源