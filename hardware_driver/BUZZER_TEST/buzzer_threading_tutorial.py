import RPi.GPIO as GPIO
import threading
import time

# =============================================================================
# 蜂鸣器配置
# =============================================================================

BUZZER_PIN = 25  # 蜂鸣器连接的GPIO引脚（BCM编号）

# 初始化GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUZZER_PIN, GPIO.OUT)

# =============================================================================
# 蜂鸣器控制线程
# =============================================================================

# 创建蜂鸣器控制事件
# threading.Event: 用于线程间通信，实现非阻塞控制
# 这个Event就像一个开关，可以控制蜂鸣器的启停
buzzer_active = threading.Event()  # 蜂鸣器激活标志

def buzzer_handler():
    """
    蜂鸣器控制线程函数
    
    功能说明:
    - 独立线程运行，不阻塞主程序
    - 使用Event机制实现非阻塞控制
    - 检测到目标时产生"滴滴"报警声
    - 资源开销极小，只包含简单的GPIO操作和sleep
    
    工作原理:
    1. 线程启动后进入等待状态
    2. 当buzzer_active被设置时，开始产生报警声
    3. 循环产生"滴滴"声（高电平0.1秒，低电平0.1秒）
    4. 当buzzer_active被清除时，停止报警并回到等待状态
    
    关键概念:
    - Event.wait(): 阻塞线程，直到Event被设置（类似等待信号）
    - Event.is_set(): 检查Event是否被设置
    - Event.set(): 设置Event，通知线程开始工作
    - Event.clear(): 清除Event，通知线程停止工作
    """
    while True:
        # 等待蜂鸣器激活信号
        # wait(): 阻塞线程，直到Event被设置
        # 资源开销：极小，只是线程挂起，不占用CPU
        # 类似于：线程在这里"睡觉"，等待被唤醒
        buzzer_active.wait()
        
        # 产生"滴滴"报警声
        # 循环执行，直到Event被清除
        while buzzer_active.is_set():
            # 高电平触发蜂鸣器（0.1秒）
            GPIO.output(BUZZER_PIN, GPIO.HIGH)
            time.sleep(0.1)
            
            # 低电平关闭蜂鸣器（0.1秒）
            GPIO.output(BUZZER_PIN, GPIO.LOW)
            time.sleep(0.1)

# 启动蜂鸣器控制线程
# daemon=True: 设置为守护线程，主程序退出时自动结束
# 资源开销：极小，线程在wait()状态时不占用CPU
buzzer_thread = threading.Thread(target=buzzer_handler, daemon=True)
buzzer_thread.start()

print("蜂鸣器控制线程已启动！")
print("输入 's' 开始蜂鸣器，输入 'e' 停止蜂鸣器")
print("输入 'q' 退出程序")
print("-" * 50)

# =============================================================================
# 主线程 - 用户输入控制
# =============================================================================

try:
    while True:
        # 获取用户输入
        # input(): 阻塞等待用户输入
        # 这里主线程会等待，但蜂鸣器线程在后台独立运行
        user_input = input("请输入命令: ").strip().lower()
        
        # 根据用户输入控制蜂鸣器
        if user_input == 's':
            # set(): 设置Event，通知蜂鸣器线程开始报警
            # 资源开销：极小，只是设置一个标志位
            # 这会唤醒正在wait()的蜂鸣器线程
            buzzer_active.set()
            print("蜂鸣器已启动！")
            
        elif user_input == 'e':
            # clear(): 清除Event，通知蜂鸣器线程停止报警
            # 资源开销：极小，只是清除一个标志位
            # 这会让蜂鸣器线程退出while循环，回到wait()状态
            buzzer_active.clear()
            print("蜂鸣器已停止！")
            
        elif user_input == 'q':
            # 退出程序
            print("正在退出程序...")
            break
            
        else:
            print("无效命令！请输入 's'、'e' 或 'q'")

except KeyboardInterrupt:
    # 处理Ctrl+C中断
    print("\n检测到中断信号，正在退出...")

finally:
    # =============================================================================
    # 资源清理
    # =============================================================================
    
    print("\n正在释放资源...")
    
    # 确保蜂鸣器停止
    buzzer_active.clear()
    
    # 确保蜂鸣器引脚为低电平
    GPIO.output(BUZZER_PIN, GPIO.LOW)
    
    # 清理GPIO资源
    GPIO.cleanup()
    
    print("资源释放完成！程序结束。")

# =============================================================================
# 教学总结
# =============================================================================

"""
【threading.Event 工作原理详解】

1. Event是什么？
   - Event是Python threading模块提供的线程同步原语
   - 它就像一个"信号"或"开关"，可以在不同线程之间传递状态

2. Event的主要方法：
   - Event.wait(): 阻塞当前线程，直到Event被set()
   - Event.set(): 设置Event标志，唤醒所有wait()的线程
   - Event.clear(): 清除Event标志
   - Event.is_set(): 检查Event是否被设置

3. 本例中的工作流程：
   
   初始状态:
   - buzzer_active = threading.Event()  # Event未设置
   - 蜂鸣器线程执行 buzzer_active.wait()  # 线程阻塞，等待
   
   用户输入 's':
   - buzzer_active.set()  # 设置Event
   - 蜂鸣器线程被唤醒  # 退出wait()，进入while循环
   - 开始产生"滴滴"声  # while buzzer_active.is_set()
   
   用户输入 'e':
   - buzzer_active.clear()  # 清除Event
   - 蜂鸣器线程退出while循环  # is_set()返回False
   - 回到wait()状态  # 再次阻塞等待

4. 为什么使用Event而不是直接控制？
   - 非阻塞：主线程可以继续接收用户输入
   - 线程安全：Event是线程安全的，不需要额外的锁
   - 资源高效：wait()状态不占用CPU资源
   - 代码清晰：逻辑分离，易于理解和维护

5. 实际应用场景：
   - 机器人控制：主线程处理传感器，子线程控制电机
   - 图像处理：主线程显示界面，子线程进行推理
   - 网络通信：主线程处理UI，子线程处理网络请求
   - 定时任务：主线程执行其他任务，子线程定时触发

【进阶技巧】

1. 可以设置超时：
   buzzer_active.wait(timeout=1.0)  # 最多等待1秒
   
2. 可以传递数据：
   使用Queue或Pipe在线程间传递复杂数据
   
3. 可以控制多个线程：
   创建多个Event，分别控制不同的线程
   
4. 可以优雅退出：
   使用Event作为退出信号，让线程安全结束
"""