from gpiozero import AngularServo
from time import sleep
from gpiozero.pins.lgpio import LGPIOFactory  # 显式导入


factory = LGPIOFactory()
# 设置舵机引脚
SERVO_PIN = 13

def main():
    try:
        # 初始化舵机
        # 注意: 调整min_pulse_width和max_pulse_width以适应你的舵机
        servo = AngularServo(SERVO_PIN, 
                            min_pulse_width=0.0005,  
                            max_pulse_width=0.0025,
                            pin_factory=factory)  
        
        # print("测试舵机控制...按Ctrl+C退出")
        # print(f"第一阶段测试：")
        
        # # 测试3个特定角度
        # servo.angle = 90
        # print(f"角度设置为:90°")
        # sleep(0.8)
        
        # servo.value = None
        # sleep(0.2)
        
        # servo.angle = 0
        # print(f"角度设置为: 0°")
        # sleep(0.8)
        
        # servo.value = None
        # sleep(0.2)
        
        # servo.angle = -90
        # print(f"角度设置为: -90°")
        # sleep(0.8)
        
        # servo.value = None
        # sleep(0.2)
                
        # 从-90度转到90度 (gpiozero使用-90到90的范围)
        while True:
            for angle in range(-90, 91 , 1):
                servo.angle = angle
                print(f"角度设置为: {angle}°")
                
                sleep(0.4)
                servo.value = None
                sleep(0.2)
                
            for angle in range(90, -91 , -1):
                servo.angle = angle
                print(f"角度设置为: {angle}°")
                
                sleep(0.4)
                servo.value = None
                sleep(0.2)
        

        
        # # 从90度转回-90度
        # for angle in range(90, -91, -30):
        #     servo.angle = angle
        #     print(f"角度设置为: {angle}°")
        #     sleep(0.4)
            
        #     servo.value = None
        #     sleep(0.1)
               
               
               
        # print(f"第二阶段测试：")
        # servo.angle = 90
        # print(f"角度设置为:90°")
        # sleep(0.8)
        
        # servo.value = None
        # sleep(2.5)
        
        # servo.angle = 0
        # print(f"角度设置为: 0°")
        # sleep(0.8)
        
        # servo.value = None
        # sleep(2.5)
        
        # servo.angle = -90
        # print(f"角度设置为: -90°")
        # sleep(0.8)    
        
        # servo.value = None
        # sleep(2.5)
        
        # servo.angle = 90
        # print(f"角度设置为:90°")
        # sleep(1)
         
    except KeyboardInterrupt:
        print("\n程序终止")

if __name__ == '__main__':
    main()