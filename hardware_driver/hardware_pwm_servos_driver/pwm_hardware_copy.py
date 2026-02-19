import time
import sys
from rpi_hardware_pwm import HardwarePWM

# --- 硬件配置 ---
# 根据你的 ls 结果：1f00098000 对应 pwmchip0
CHIP_ID = 0  

# GPIO 12 -> PWM0_CHAN0 -> channel 0 (TILT 轴)
# GPIO 13 -> PWM0_CHAN1 -> channel 1 (PAN 轴)
TILT_CHANNEL = 0
PAN_CHANNEL = 1

def main():
    try:
        print(f"正在初始化硬件 PWM (Chip {CHIP_ID})...")
        
        # 初始化两个通道
        servo_tilt = HardwarePWM(pwm_channel=TILT_CHANNEL, hz=50, chip=CHIP_ID)
        servo_pan = HardwarePWM(pwm_channel=PAN_CHANNEL, hz=50, chip=CHIP_ID)
        
        # 启动，初始占空比 7.5% (对应 0度)
        servo_tilt.start(7.5)
        servo_pan.start(7.5)
        
        print("硬件通道已开启。开始同步步进测试...")

        def set_angle(pwm_obj, angle):
            """将角度(-90到90)映射为硬件占空比(2.5到12.5)"""
            angle = max(-90, min(90, angle))
            duty = (angle + 90) * (10 / 180) + 2.5
            pwm_obj.change_duty_cycle(duty)

        
            # 1度步进扫描
        for angle in range(-90, 91, 1):
            set_angle(servo_pan, angle)
            set_angle(servo_tilt, angle)
            print(f"当前角度: {angle}° ", end='\r')
            time.sleep(0.02) # 硬件PWM响应快，可以设置更短的延迟
                
        for angle in range(90, -91, -1):
            set_angle(servo_pan, angle)
            set_angle(servo_tilt, angle)
            print(f"当前角度: {angle}° ", end='\r')
            time.sleep(0.02)
            
        for angle in range(-90, 91, 30):
            set_angle(servo_pan, angle)
            set_angle(servo_tilt, angle)
            print(f"当前角度: {angle}° ", end='\r')
            time.sleep(0.5)
        
        for angle in range(90, -91, 90):
            set_angle(servo_pan, angle)
            set_angle(servo_tilt, angle)
            print(f"当前角度: {angle}° ", end='\r')
            time.sleep(1.5)
            
        for angle in range(-90, 91, 90):
            set_angle(servo_pan, angle)
            set_angle(servo_tilt, angle)
            print(f"当前角度: {angle}° ", end='\r')
            time.sleep(1.5)
            
    except KeyboardInterrupt:
        print("\n测试由用户停止")
    except Exception as e:
        print(f"\n发生错误: {e}")
    finally:
        # 停止 PWM 输出
        try:
            servo_tilt.stop()
            servo_pan.stop()
            print("硬件 PWM 已释放")
        except:
            pass

if __name__ == '__main__':
    main()
