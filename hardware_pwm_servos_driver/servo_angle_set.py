import time
import sys
from rpi_hardware_pwm import HardwarePWM

# --- 硬件配置 ---
# 根据你的 ls 结果，f00098000 对应 pwmchip0
CHIP_ID = 0  
# GPIO 12 -> PWM0_CHAN0 -> channel 0 (TILT 轴)
# GPIO 13 -> PWM0_CHAN1 -> channel 1 (PAN 轴)
TILT_CHANNEL = 0
PAN_CHANNEL = 1

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
        servo_tilt.start(7.5)
        servo_pan.start(7.5)
        
        print("硬件通道已开启。开始同步扫描测试...")
        print("按 Ctrl+C 停止测试")
        print("给两个舵机角度归零")
        set_angle(servo_pan, 0)
        set_angle(servo_tilt, 0)
        time.sleep(3)
        print("角度设定完毕")
        # # 单次扫描测试
        # print("\n开始单次扫描...")
        
        # # 从 -90° 到 +90°
        # for angle in range(0, 91, 1):
        #     set_angle(servo_pan, angle)
        #     set_angle(servo_tilt, angle)
        #     print(f"当前角度: {angle:+4d}°", end='\r')
        #     time.sleep(0.02)
        
        # # 从 +90° 到 -90°
        # for angle in range(91, -91, -1):
        #     set_angle(servo_pan, angle)
        #     set_angle(servo_tilt, angle)
        #     print(f"当前角度: {angle:+4d}°", end='\r')
        #     time.sleep(0.02)
            
        # # 从 +90° 到 -90°
        # for angle in range(-91, 0, 1):
        #     set_angle(servo_pan, angle)
        #     set_angle(servo_tilt, angle)
        #     print(f"当前角度: {angle:+4d}°", end='\r')
        #     time.sleep(0.02)
        
        # # 回到中心位置
        # print("\n返回中心位置 (0°)...")
        # set_angle(servo_pan, 0)
        # set_angle(servo_tilt, 0)
        # time.sleep(1)
        
        # print("单次扫描完成！")
        
    except KeyboardInterrupt:
        print("\n测试由用户停止")
    except Exception as e:
        print(f"\n发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 停止 PWM 输出
        try:
            print("\n正在关闭 PWM...")
            servo_tilt.stop()
            servo_pan.stop()
            print("硬件 PWM 已释放")
        except:
            pass

if __name__ == '__main__':
    main()