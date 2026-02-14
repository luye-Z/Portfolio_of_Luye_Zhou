import time
import sys
from rpi_hardware_pwm import HardwarePWM

# --- 硬件配置 ---
# 根据你的 ls 结果，f00098000 对应 pwmchip0
CHIP_ID = 0  
# GPIO 12 -> PWM0_CHAN0 -> channel 0 (TILT 轴)
# GPIO 13 -> PWM0_CHAN1 -> channel 1 (PAN 轴)
TILT_CHANNEL = 1 #GPIO13
PAN_CHANNEL = 0 #GPIO12

 
SERVO_STEP_DELAY = 0.01

def set_angle(pwm_obj, angle):
    """将角度(-90到90)映射为硬件占空比(2.5到12.5)"""
    angle = max(-90, min(90, angle))
    duty = (angle + 90) * (10 / 180) + 2.5
    pwm_obj.change_duty_cycle(duty)

def main():
    try:
        print(f"正在初始化硬件 PWM (Chip {CHIP_ID})...")
        
        # 初始化两个通道
        servo_tilt = HardwarePWM(pwm_channel=TILT_CHANNEL, hz=50, chip=CHIP_ID)
        servo_pan = HardwarePWM(pwm_channel=PAN_CHANNEL, hz=50, chip=CHIP_ID)
        
        # 启动，初始占空比 7.5% (对应 0度)
        servo_tilt.start(12.5)
        servo_pan.start(7.5)
        
        print("硬件通道已开启。开始同步扫描测试...")
        print("按 Ctrl+C 停止测试")
        
        # 单次扫描测试
        print("\n开始单次扫描...")
        
        # 从 -90° 到 +90°
        
        for angle in range(90, -91 , -1):  #range 的范围，包含起点不包含终点
            # set_angle(servo_pan, angle)
            set_angle(servo_tilt, angle)
            print(f"舵机选择：servo_tilt，当前角度: {angle:+4d}°", end='\r')
            time.sleep(SERVO_STEP_DELAY)
            
        
        for angle in range(-90, 91 , 1):  #range 的范围，包含起点不包含终点
            # set_angle(servo_pan, angle)
            set_angle(servo_tilt, angle)
            print(f"舵机选择：servo_tilt，当前角度: {angle:+4d}°", end='\r')
            time.sleep(SERVO_STEP_DELAY)
            
        
        for angle in range(0, -91 , -1):  #range 的范围，包含起点不包含终点
            set_angle(servo_pan, angle)
            #set_angle(servo_tilt, angle)
            print(f"舵机选择：servo_pan，当前角度: {angle:+4d}°", end='\r')
            time.sleep(SERVO_STEP_DELAY)
            
        
        for angle in range(-90, 91 , 1):  #range 的范围，包含起点不包含终点
            set_angle(servo_pan, angle)
            #set_angle(servo_tilt, angle)
            print(f"舵机选择：servo_pan，当前角度: {angle:+4d}°", end='\r')
            time.sleep(SERVO_STEP_DELAY)
            
        
        for angle in range(90, -1 , -1):  #range 的范围，包含起点不包含终点
            set_angle(servo_pan, angle)
            #set_angle(servo_tilt, angle)
            print(f"舵机选择：servo_pan，当前角度: {angle:+4d}°", end='\r')
            time.sleep(SERVO_STEP_DELAY)
            
            
        # for angle in range(90, -91, -1):  #range 的范围，包含起点不包含终点
        #     # set_angle(servo_pan, angle)
        #     set_angle(servo_tilt, angle)
        #     print(f"当前角度: {angle:+4d}°", end='\r')
        #     time.sleep(0.05)
            
        # for angle in range(-90, 1, 1):  #range 的范围，包含起点不包含终点
        #     # set_angle(servo_pan, angle)
        #     set_angle(servo_tilt, angle)
        #     print(f"当前角度: {angle:+4d}°", end='\r')
        #     time.sleep(0.05)
            
        # for angle in range(90, -1, -1):  #range 的范围，包含起点不包含终点
        #     set_angle(servo_pan, angle)
        #     # set_angle(servo_tilt, angle)
        #     print(f"当前角度: {angle:+4d}°", end='\r')
        #     time.sleep(0.05)
        # # 从 +90° 到 -90°
        # for angle in range(90, -91, -1):
        #     set_angle(servo_pan, angle)
        #     set_angle(servo_tilt, angle)
        #     print(f"当前角度: {angle:+4d}°", end='\r')
        #     time.sleep(0.2)
            
        # # 从 +90° 到 -90°
        # for angle in range(-90, 1, 1):
        #     set_angle(servo_pan, angle)
        #     set_angle(servo_tilt, angle)
        #     print(f"当前角度: {angle:+4d}°", end='\r')
        #     time.sleep(0.2)
        
        # 回到中心位置
        print("\n返回中心位置 ")
        set_angle(servo_pan, 0)
        set_angle(servo_tilt, 90)
        print(f"servo_pan 角度: {0:+4d}°")
        print(f"servo_tilt 角度: {90:+4d}°")
        
        time.sleep(1)
        
        print("单次扫描完成！")
        
    except KeyboardInterrupt:
        print("\n测试由用户停止")
    except Exception as e:
        print(f"\n发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 停止 PWM 输出
        try:
            set_angle(servo_pan, 0)
            set_angle(servo_tilt, 90)
            time.sleep(0.5)  # 必须等待！
            print("\n正在关闭 PWM...")
            servo_tilt.stop()
            servo_pan.stop()
            print("硬件 PWM 已释放")
        except:
            print("关闭时候出错")
            pass

if __name__ == '__main__':
    main()