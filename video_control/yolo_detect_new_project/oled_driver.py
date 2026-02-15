import time
import threading
import queue
from PIL import ImageFont
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306


class OLED_Driver:
    """SSD1306 OLED 屏幕驱动类（后台线程版）
    
    特性：
    - 后台线程处理显示，不阻塞主线程
    - 使用队列传递显示任务
    - 线程安全的接口
    
    使用示例：
        # 方式1：使用with语句（推荐）
        with OLED_Driver() as oled:
            oled.text("Hello, World!")  # 不阻塞，立即返回
            time.sleep(2)
            oled.clear()
        
        # 方式2：手动管理
        oled = OLED_Driver()
        oled.text("Hello!")
        oled.stop()
    """
    
    def __init__(self, port=1, address=0x3C):
        """初始化 OLED 屏幕
        
        参数:
            port: I2C 总线端口（默认 1）
            address: I2C 地址（默认 0x3C）
        """
        self.port = port
        self.address = address
        self.width = 128
        self.height = 64
        self.font_path = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"
        self.device = None
        self.font_cache = {}
        
        # 线程相关
        self._display_queue = queue.Queue(maxsize=5)  # 显示任务队列
        self._stop_event = threading.Event()  # 停止事件
        self._thread = None  # 后台线程
        self._running = False
        
        # 初始化设备
        self._init_device()
        
        # 启动后台线程
        self._start_thread()
    
    def _init_device(self):
        """内部方法：初始化设备"""
        try:
            serial = i2c(port=self.port, address=self.address)
            self.device = ssd1306(serial, width=self.width, height=self.height)
            print(f"[OLED] 初始化成功 - {self.width}x{self.height}")
        except Exception as e:
            raise RuntimeError(f"OLED 初始化失败: {e}")
    
    def _get_font(self, size):
        """内部方法：获取字体对象（带缓存）"""
        if size not in self.font_cache:
            self.font_cache[size] = ImageFont.truetype(self.font_path, size)
        return self.font_cache[size]
    
    def _display_thread(self):
        """后台显示线程"""
        print("[OLED] 后台显示线程已启动")
        
        while not self._stop_event.is_set():
            try:
                # 从队列获取任务，最多等待 0.1 秒
                try:
                    task = self._display_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                
                # 执行任务
                task_type = task['type']
                
                if task_type == 'text':
                    self._do_text(task)
                elif task_type == 'clear':
                    self._do_clear()
                
                # 标记任务完成
                self._display_queue.task_done()
                
            except Exception as e:
                print(f"[OLED] 显示错误: {e}")
                time.sleep(0.1)
        
        print("[OLED] 后台显示线程已停止")
    
    def _do_text(self, task):
        """内部方法：执行文本显示"""
        if not self.device:
            return
        
        content = task['content']
        size = task['size']
        center = task['center']
        
        font = self._get_font(size)
        
        with canvas(self.device) as draw:
            draw.rectangle(self.device.bounding_box, outline="white", fill="black")
            
            lines = content.split('\\n')
            line_heights = []
            
            for line in lines:
                ascent, descent = font.getmetrics()
                line_heights.append(ascent - descent + 2)
            
            if center:
                total_height = sum(line_heights)
                start_y = (self.height - total_height) // 2
            else:
                start_y = 1
            
            current_y = start_y
            
            for i, line in enumerate(lines):
                if not line.strip():
                    current_y += line_heights[i]
                    continue
                
                w = font.getlength(line)
                
                if center:
                    x = (self.width - w) // 2
                else:
                    x = 10
                
                y = current_y
                draw.text((x, y), line, font=font, fill="white")
                current_y += line_heights[i]
    
    def _do_clear(self):
        """内部方法：执行清屏"""
        if not self.device:
            return
        
        with canvas(self.device) as draw:
            draw.rectangle(self.device.bounding_box, outline="black", fill="black")
    
    def _start_thread(self):
        """内部方法：启动后台线程"""
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._display_thread, daemon=True)
        self._thread.start()
        self._running = True
    
    def text(self, content, size=12, center=True):
        """在屏幕上显示文本（不阻塞主线程）
        
        参数:
            content: 要显示的文本（支持换行 \\n）
            size: 字体大小（默认 12）
            center: 是否居中显示（默认 True）
        """
        if not self._running:
            return
        
        # 把显示任务放入队列，立即返回
        try:
            self._display_queue.put({
                'type': 'text',
                'content': content,
                'size': size,
                'center': center
            }, block=False)
        except queue.Full:
            # 队列满了，丢弃最旧的任务
            try:
                self._display_queue.get_nowait()
                self._display_queue.put({
                    'type': 'text',
                    'content': content,
                    'size': size,
                    'center': center
                }, block=False)
            except queue.Empty:
                pass
    
    def clear(self):
        """清屏（不阻塞主线程）"""
        if not self._running:
            return
        
        try:
            self._display_queue.put({'type': 'clear'}, block=False)
        except queue.Full:
            pass
    
    def stop(self):
        """停止后台线程并释放资源"""
        if not self._running:
            return
        
        print("[OLED] 正在停止后台线程...")
        
        # 设置停止事件
        self._stop_event.set()
        
        # 等待线程结束（最多等待 2 秒）
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        
        # 清屏
        self._do_clear()
        
        # 关闭设备
        if self.device is not None:
            try:
                self.device.cleanup()
                print("[OLED] 设备已关闭")
            except Exception as e:
                print(f"[OLED] 关闭设备时出错: {e}")
            finally:
                self.device = None
        
        self._running = False
    
    def cleanup(self):
        """释放所有资源（同 stop）"""
        self.stop()
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.cleanup()
        return False
    
    def __del__(self):
        """析构函数，确保资源释放"""
        self.cleanup()


# --- 测试代码 ---
if __name__ == "__main__":
    print("=" * 50)
    print("OLED 后台线程版驱动测试")
    print("=" * 50)
    
    with OLED_Driver() as oled:
        print("\n[测试1] 显示单行文本（不阻塞）")
        oled.text("禄也，您好")  # 不阻塞，立即返回
        print("  已提交显示任务")
        time.sleep(2)
        
        print("\n[测试2] 显示多行文本（不阻塞）")
        oled.text("多行文本\\n第2行\\n第3行", size=10)
        print("  已提交显示任务")
        time.sleep(2)
        
        print("\n[测试3] 不居中显示（不阻塞）")
        oled.text("不居中显示", center=False)
        print("  已提交显示任务")
        time.sleep(2)
        
        print("\n[测试4] 清屏（不阻塞）")
        oled.clear()
        print("  已提交清屏任务")
        time.sleep(1)
        
        print("\n[测试5] 快速连续显示（不阻塞）")
        for i in range(5):
            oled.text(f"快速显示 {i+1}")
            print(f"  已提交显示任务 {i+1}")
            time.sleep(0.5)
    
    print("\n测试完成！")
