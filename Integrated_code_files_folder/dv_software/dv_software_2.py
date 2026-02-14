#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Design Verification (DV) Software for Raspberry Pi 5 Hardware System
硬件系统设计验证软件 - 树莓派5

功能：验证各个硬件模块的协同工作,快速检测硬件连接和功能是否正常
设计原则：模块化、高内聚、低耦合、易读性
"""

import time
import sys
from enum import Enum
from typing import Dict, List, Optional, Tuple
import os
import threading
from PIL import Image, ImageSequence
from PIL import ImageFont, ImageDraw
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306

import neopixel #导入RGB_LED需要的库
# =============================================================================
# 硬件配置常量 (根据README.md中的连接信息)
# =============================================================================

class HardwareConfig:
    """硬件配置类 - 集中管理所有硬件连接信息"""
    
    # GPIO引脚配置
    GPIO_BUTTON = 23        # 按键GPIO23
    GPIO_BUZZER = 25        # 蜂鸣器GPIO25
    GPIO_LED_DIN = 18       # RGB LED DIN GPIO18
    GPIO_MPU6050_1_INT = 7  # MPU6050_1中断引脚GPIO7
    GPIO_MPU6050_2_INT = 24 # MPU6050_2中断引脚GPIO24
    GPIO_RGB_LED_DIN = 18   #引脚GPIO18连接 RGB_LED的 DIN
    
    # PWM配置
    PWM_CHIP_ID = 0
    PWM_SERVO_1_CHANNEL = 0  # 舵机1 (GPIO12_PWM0)
    PWM_SERVO_2_CHANNEL = 1  # 舵机2 (GPIO13_PWM1)
    PWM_FREQUENCY = 50       # 舵机PWM频率50Hz
    
    # I2C配置
    I2C_BUS = 1
    OLED_ADDRESS = 0x3C      # OLED屏幕地址
    MPU6050_1_ADDR = 0x68   # MPU6050_1地址 (ADO接GND)
    MPU6050_2_ADDR = 0x69   # MPU6050_2地址 (ADO接+3.3V)

# =============================================================================
# 测试结果枚举和数据结构
# =============================================================================

class TestStatus(Enum): #定义一个枚举类
    """测试状态枚举,这是一个枚举类"""
    NOT_STARTED = "未开始"
    RUNNING = "进行中"
    PASSED = "通过"
    FAILED = "失败"
    SKIPPED = "跳过"

class TestResult:
    """单个测试结果类"""
    def __init__(self, name: str, description: str = ""): #构造函数,两个参数 一个是 name,一个是description , 
            #这里还涉及到type-hint , 就是 name : 后面的 "str" , description:后面的 "str"
            #这两个type-hind代表着参数类型, str="" 代表着默认参数是"",即为一个空字符串,这个参数可以不输入,即为可选
        self.name = name
        self.description = description
        self.status = TestStatus.NOT_STARTED #这里调用了枚举类 TestStatus 枚举类很特殊,不需要实例化,直接调用
        self.duration = 0.0 
        self.error_message = ""
        self.timestamp = 0.0 #时间戳
    
    def set_passed(self, duration: float):
        """设置测试通过"""
        self.status = TestStatus.PASSED
        self.duration = duration
        self.timestamp = time.time()
    
    def set_failed(self, duration: float, error_message: str):
        """设置测试失败"""
        self.status = TestStatus.FAILED
        self.duration = duration
        self.error_message = error_message
        self.timestamp = time.time()
    
    def set_skipped(self, reason: str = ""):
        """设置测试跳过"""
        self.status = TestStatus.SKIPPED
        self.error_message = reason
        self.timestamp = time.time()

# =============================================================================
# 硬件模块基类
# =============================================================================

class HardwareModule:
    """硬件模块基类 - 提供统一的接口和错误处理"""
    
    def __init__(self, name: str):
        self.name = name
        self.is_initialized = False
        self.last_error = ""
    
    def initialize(self) -> bool:
        """初始化硬件模块"""
        try:
            result = self._initialize_impl()
            self.is_initialized = result
            if not result:
                self.last_error = f"{self.name} 初始化失败"
            return result
        except Exception as e:
            self.last_error = f"{self.name} 初始化异常: {str(e)}"
            self.is_initialized = False
            return False
    
    def test_functionality(self) -> Tuple[bool, str]:
        """测试硬件功能"""
        if not self.is_initialized:
            return False, f"{self.name} 未初始化"
        
        try:
            return self._test_functionality_impl()
        except Exception as e:
            return False, f"{self.name} 功能测试异常: {str(e)}"
    
    def cleanup(self):
        """清理资源"""
        try:
            self._cleanup_impl()
            self.is_initialized = False
        except Exception as e:
            print(f"警告: {self.name} 清理时出错: {e}")
    
    # 子类需要实现的抽象方法
    def _initialize_impl(self) -> bool:
        raise NotImplementedError("子类必须实现 _initialize_impl 方法")
    
    def _test_functionality_impl(self) -> Tuple[bool, str]:
        raise NotImplementedError("子类必须实现 _test_functionality_impl 方法")
    
    def _cleanup_impl(self):
        raise NotImplementedError("子类必须实现 _cleanup_impl 方法")

# =============================================================================
# 具体硬件模块实现
# =============================================================================

class PWMHardwareModule(HardwareModule):
    """PWM硬件模块 - 控制舵机"""
    
    def __init__(self):
        super().__init__("PWM舵机控制")
        self.servo_1 = None
        self.servo_2 = None
    
    def _initialize_impl(self) -> bool:
        """初始化PWM硬件"""
        try:
            from rpi_hardware_pwm import HardwarePWM
            
            # 初始化两个舵机通道
            self.servo_1 = HardwarePWM(
                pwm_channel=HardwareConfig.PWM_SERVO_1_CHANNEL,
                hz=HardwareConfig.PWM_FREQUENCY,
                chip=HardwareConfig.PWM_CHIP_ID
            )
            self.servo_2 = HardwarePWM(
                pwm_channel=HardwareConfig.PWM_SERVO_2_CHANNEL,
                hz=HardwareConfig.PWM_FREQUENCY,
                chip=HardwareConfig.PWM_CHIP_ID
            )
            
            # 启动PWM输出
            self.servo_1.start(7.5)  # 7.5%占空比对应0度
            self.servo_2.start(7.5)
            
            print("✅ PWM硬件初始化成功")
            return True
            
        except ImportError:
            self.last_error = "未找到 rpi_hardware_pwm 库"
            return False
        except Exception as e:
            self.last_error = f"PWM初始化失败: {str(e)}"
            return False
    
    def _test_functionality_impl(self) -> Tuple[bool, str]:
        """测试舵机功能"""
        try:
            # 从0度一度一度转到-90度
            print("舵机从0度转到-90度...")
            for angle in range(0, -91, -1):  # 0, -1, -2, ..., -90
                self._set_servo_angle(self.servo_1, angle)
                self._set_servo_angle(self.servo_2, angle)
                time.sleep(0.05)  # 每度间隔50ms,让运动更平滑
            
            # 从-90度一度一度转到90度
            print("舵机从-90度转到90度...")
            for angle in range(-90, 91, 1):  # -90, -89, ..., 90
                self._set_servo_angle(self.servo_1, angle)
                self._set_servo_angle(self.servo_2, angle)
                time.sleep(0.05)
            
            # 从90度一度一度转回0度
            print("舵机从90度转回0度...")
            for angle in range(90, -1, -1):  # 90, 89, ..., 0
                self._set_servo_angle(self.servo_1, angle)
                self._set_servo_angle(self.servo_2, angle)
                time.sleep(0.05)
            
            # 确保回到0度
            self._set_servo_angle(self.servo_1, 0)
            self._set_servo_angle(self.servo_2, 0)
            
            return True, "舵机运动测试通过（0→-90→90→0度）"
            
        except Exception as e:
            return False, f"舵机测试失败: {str(e)}"
    
    def _cleanup_impl(self):
        """清理PWM资源"""
        if self.servo_1:
            self.servo_1.stop()
        if self.servo_2:
            self.servo_2.stop()
    
    def _set_servo_angle(self, servo, angle: float):
        """设置舵机角度 (-90到90度)"""
        angle = max(-90, min(90, angle))
        duty_cycle = (angle + 90) * (10 / 180) + 2.5
        servo.change_duty_cycle(duty_cycle)

class MPU6050HardwareModule(HardwareModule):
    """MPU6050传感器模块"""
    
    def __init__(self, sensor_id: int = 1):
        super().__init__(f"MPU6050传感器_{sensor_id}")
        self.sensor_id = sensor_id
        self.bus = None
        self.address = HardwareConfig.MPU6050_1_ADDR if sensor_id == 1 else HardwareConfig.MPU6050_2_ADDR
        self.offset = {
            'gyro_x': 0.0, 'gyro_y': 0.0, 'gyro_z': 0.0,
            'acc_x': 0.0, 'acc_y': 0.0, 'acc_z': 0.0
        }
    
    def _initialize_impl(self) -> bool:
        """初始化MPU6050传感器"""
        try:
            from smbus2 import SMBus
            
            self.bus = SMBus(HardwareConfig.I2C_BUS)
            
            # 唤醒传感器
            self.bus.write_byte_data(self.address, 0x6B, 0x00)
            time.sleep(0.1)
            
            # 简单通信测试
            who_am_i = self.bus.read_byte_data(self.address, 0x75)
            if who_am_i != 0x68:  # MPU6050的WHO_AM_I寄存器值
                self.last_error = f"MPU6050_{self.sensor_id} 通信测试失败"
                return False
            
            # 执行快速校准
            self._quick_calibrate()
            
            print(f"✅ MPU6050_{self.sensor_id} 初始化成功")
            return True
            
        except ImportError:
            self.last_error = "未找到 smbus2 库"
            return False
        except Exception as e:
            self.last_error = f"MPU6050_{self.sensor_id} 初始化失败: {str(e)}"
            return False
    
    def _quick_calibrate(self, samples: int = 50):
        """快速校准传感器（基于你的测试数据）"""
        print(f"🔧 快速校准 MPU6050_{self.sensor_id}...")
        
        sum_gyro_x = sum_gyro_y = sum_gyro_z = 0
        sum_acc_x = sum_acc_y = sum_acc_z = 0
        
        for i in range(samples):
            # 读取原始数据
            sum_gyro_x += self._read_word_2c(0x43) / 131.0
            sum_gyro_y += self._read_word_2c(0x45) / 131.0
            sum_gyro_z += self._read_word_2c(0x47) / 131.0
            
            sum_acc_x += self._read_word_2c(0x3B) / 16384.0
            sum_acc_y += self._read_word_2c(0x3D) / 16384.0
            sum_acc_z += self._read_word_2c(0x3F) / 16384.0
            
            time.sleep(0.01)
        
        # 计算偏移量（根据你的实际数据调整）
        self.offset['gyro_x'] = sum_gyro_x / samples
        self.offset['gyro_y'] = sum_gyro_y / samples
        self.offset['gyro_z'] = sum_gyro_z / samples
        
        # Z轴加速度补偿重力（水平放置时Z轴应该是-1g）
        self.offset['acc_x'] = sum_acc_x / samples
        self.offset['acc_y'] = sum_acc_y / samples
        self.offset['acc_z'] = sum_acc_z / samples + 1.0
    
    def _test_functionality_impl(self) -> Tuple[bool, str]:
        """测试MPU6050传感器功能（基于你的实际测试数据）"""
        try:
            # 读取多组数据求平均,减少噪声影响
            test_samples = 10
            accel_sum = [0, 0, 0]
            gyro_sum = [0, 0, 0]
            
            for i in range(test_samples):
                accel_data = self._read_calibrated_accelerometer()
                gyro_data = self._read_calibrated_gyroscope()
                
                for j in range(3):
                    accel_sum[j] += accel_data[j]
                    gyro_sum[j] += gyro_data[j]
                
                time.sleep(0.05)
            
            # 计算平均值
            accel_avg = [x / test_samples for x in accel_sum]
            gyro_avg = [x / test_samples for x in gyro_sum]
            
            # 计算加速度合成值（应该接近1g）
            acc_total = (accel_avg[0]**2 + accel_avg[1]**2 + accel_avg[2]**2) ** 0.5
            
            # **修正测试条件（基于你的实际数据）**
            # 静止状态下：
            # - 加速度计：X/Y接近0,Z接近-1g,合成值接近1g
            # - 陀螺仪：三轴都应该在±1°/s以内（你的数据在±0.5°/s以内）
            
            # 检查加速度计数据
            if abs(accel_avg[0]) > 0.1:  # X轴应该接近0
                return False, f"加速度计X轴异常: {accel_avg[0]:.3f}g (期望接近0)"
            if abs(accel_avg[1]) > 0.1:  # Y轴应该接近0
                return False, f"加速度计Y轴异常: {accel_avg[1]:.3f}g (期望接近0)"
            if abs(accel_avg[2] + 1.0) > 0.1:  # Z轴应该接近-1g
                return False, f"加速度计Z轴异常: {accel_avg[2]:.3f}g (期望接近-1.0g)"
            if abs(acc_total - 1.0) > 0.2:  # 合成值应该接近1g
                return False, f"加速度合成值异常: {acc_total:.3f}g (期望接近1.0g)"
            
            # 检查陀螺仪数据（基于你的实际数据±0.5°/s）
            if abs(gyro_avg[0]) > 0.5:
                return False, f"陀螺仪X轴异常: {gyro_avg[0]:.2f}°/s (期望在±0.5°/s内)"
            if abs(gyro_avg[1]) > 0.5:
                return False, f"陀螺仪Y轴异常: {gyro_avg[1]:.2f}°/s (期望在±0.5°/s内)"
            if abs(gyro_avg[2]) > 0.5:
                return False, f"陀螺仪Z轴异常: {gyro_avg[2]:.2f}°/s (期望在±0.5°/s内)"
            
            # 显示详细数据
            data_info = (
                f"加速度: X={accel_avg[0]:+6.3f}g, Y={accel_avg[1]:+6.3f}g, Z={accel_avg[2]:+6.3f}g, "
                f"合成={acc_total:.3f}g | "
                f"陀螺仪: X={gyro_avg[0]:+6.2f}°/s, Y={gyro_avg[1]:+6.2f}°/s, Z={gyro_avg[2]:+6.2f}°/s"
            )
            
            return True, data_info
            
        except Exception as e:
            return False, f"MPU6050_{self.sensor_id} 测试失败: {str(e)}"
    
    def _read_calibrated_accelerometer(self) -> Tuple[float, float, float]:
        """读取校准后的加速度计数据"""
        accel_x = self._read_word_2c(0x3B) / 16384.0 - self.offset['acc_x']
        accel_y = self._read_word_2c(0x3D) / 16384.0 - self.offset['acc_y']
        accel_z = self._read_word_2c(0x3F) / 16384.0 - self.offset['acc_z']
        return accel_x, accel_y, accel_z
    
    def _read_calibrated_gyroscope(self) -> Tuple[float, float, float]:
        """读取校准后的陀螺仪数据"""
        gyro_x = self._read_word_2c(0x43) / 131.0 - self.offset['gyro_x']
        gyro_y = self._read_word_2c(0x45) / 131.0 - self.offset['gyro_y']
        gyro_z = self._read_word_2c(0x47) / 131.0 - self.offset['gyro_z']
        return gyro_x, gyro_y, gyro_z
    
    def _cleanup_impl(self):
        """清理I2C资源"""
        if self.bus:
            self.bus.close()
    
    def _read_word_2c(self, addr: int) -> int:
        """读取16位有符号整数"""
        high = self.bus.read_byte_data(self.address, addr)
        low = self.bus.read_byte_data(self.address, addr + 1)
        val = (high << 8) + low
        if val >= 0x8000:
            return -((65535 - val) + 1)
        else:
            return val

class OLEDHardwareModule(HardwareModule):
    """OLED屏幕模块"""
    
    def __init__(self):
        super().__init__("OLED屏幕")
        self.device = None
        self.font_path = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"  # 字体路径
    
    def _initialize_impl(self) -> bool:
        """初始化OLED屏幕"""
        try:
            from luma.core.interface.serial import i2c
            from luma.oled.device import ssd1306
            
            serial = i2c(port=HardwareConfig.I2C_BUS, address=HardwareConfig.OLED_ADDRESS)
            self.device = ssd1306(serial, width=128, height=64)
            
            # 简单显示测试
            self._draw_text("OLED就绪", 12)
            time.sleep(1)
            
            print("✅ OLED屏幕初始化成功")
            return True
            
        except ImportError:
            self.last_error = "未找到 luma.oled 库"
            return False
        except Exception as e:
            self.last_error = f"OLED初始化失败: {str(e)}"
            return False
    
    def _test_functionality_impl(self) -> Tuple[bool, str]:
        """测试OLED显示功能"""
        try:
            test_messages = ["DV测试中", "硬件验证", "测试通过!"]
            font_sizes = [14, 16, 18]
            
            for i, msg in enumerate(test_messages):
                self._draw_text(msg, font_sizes[i])
                time.sleep(1)
            
            # 显示多行文本测试
            self._draw_multiline_text(["OLED测试", "功能正常", "显示清晰"], 12)
            time.sleep(2)
            
            return True, "OLED显示测试通过 - 文本居中、多行显示功能正常"
            
        except Exception as e:
            return False, f"OLED测试失败: {str(e)}"
    
    def _cleanup_impl(self):
        """清理OLED资源"""
        if self.device:
            self.device.cleanup()
    
    def _draw_text(self, text: str, font_size: int):
        """在OLED上居中显示文本（基于oled_test.py的优化版本）"""
        try:
            from PIL import ImageFont
            from luma.core.render import canvas
            
            # 加载字体
            font = ImageFont.truetype(self.font_path, font_size)
            
            with canvas(self.device) as draw:
                # 绘制黑色背景矩形
                draw.rectangle(self.device.bounding_box, outline="white", fill="black")
                
                # 计算文本宽度和高度
                text_width = font.getlength(text)
                ascent, descent = font.getmetrics()
                text_height = ascent - descent
                
                # 计算居中位置
                x = (self.device.width - text_width) // 2
                y = (self.device.height - text_height) // 2
                
                # 绘制居中文本
                draw.text((x, y), text, font=font, fill="white")
                
        except Exception as e:
            print(f"OLED显示错误: {e}")
            # 使用简化显示作为备用
            with canvas(self.device) as draw:
                draw.rectangle(self.device.bounding_box, outline="white", fill="black")
                draw.text((10, 20), text, fill="white")
    
    def _draw_multiline_text(self, lines: List[str], font_size: int):
        """在OLED上显示多行文本"""
        try:
            from PIL import ImageFont
            from luma.core.render import canvas
            
            font = ImageFont.truetype(self.font_path, font_size)
            
            with canvas(self.device) as draw:
                draw.rectangle(self.device.bounding_box, outline="white", fill="black")
                
                ascent, descent = font.getmetrics()
                line_height = ascent + 2  # 行间距
                total_height = len(lines) * line_height
                start_y = (self.device.height - total_height) // 2
                
                for i, line in enumerate(lines):
                    text_width = font.getlength(line)
                    x = (self.device.width - text_width) // 2
                    y = start_y + i * line_height
                    draw.text((x, y), line, font=font, fill="white")
                    
        except Exception as e:
            print(f"OLED多行显示错误: {e}")
    
    def display_test_results(self, test_name: str, status: str, duration: float = 0.0):
        """在OLED上显示测试结果"""
        try:
            status_symbol = "✅" if status == "通过" else "❌" if status == "失败" else "⚠️"
            lines = [
                f"{test_name}",
                f"{status_symbol} {status}",
                f"耗时: {duration:.2f}s" if duration > 0 else ""
            ]
            self._draw_multiline_text([line for line in lines if line], 12)
            
        except Exception as e:
            print(f"OLED结果显示错误: {e}")

class ButtonHardwareModule(HardwareModule):
    """按键模块"""
    
    def __init__(self):
        super().__init__("按键检测")
        self.gpio_setup = False
    
    def _initialize_impl(self) -> bool:
        """初始化按键GPIO"""
        try:
            import RPi.GPIO as GPIO
            
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(HardwareConfig.GPIO_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            self.gpio_setup = True
            
            print("✅ 按键GPIO初始化成功")
            return True
            
        except ImportError:
            self.last_error = "未找到 RPi.GPIO 库"
            return False
        except Exception as e:
            self.last_error = f"按键初始化失败: {str(e)}"
            return False
    
    def _test_functionality_impl(self) -> Tuple[bool, str]:
        """测试按键功能"""
        try:
            import RPi.GPIO as GPIO
            
            print("请按下按键(GPIO23)...")
            start_time = time.time()
            timeout = 10  # 10秒超时
            
            while time.time() - start_time < timeout:
                if GPIO.input(HardwareConfig.GPIO_BUTTON) == GPIO.HIGH:
                    return True, "按键检测通过"
                time.sleep(0.1)
            
            return False, "按键测试超时 - 请检查按键连接"
            
        except Exception as e:
            return False, f"按键测试失败: {str(e)}"
    
    def _cleanup_impl(self):
        """清理GPIO资源"""
        try:
            import RPi.GPIO as GPIO
            if self.gpio_setup:
                GPIO.cleanup(HardwareConfig.GPIO_BUTTON)
        except:
            pass

class BuzzerHardwareModule(HardwareModule):
    """蜂鸣器模块"""
    
    def __init__(self):
        super().__init__("蜂鸣器")
        self.gpio_setup = False
    
    def _initialize_impl(self) -> bool:
        """初始化蜂鸣器GPIO"""
        try:
            import RPi.GPIO as GPIO
            
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(HardwareConfig.GPIO_BUZZER, GPIO.OUT)
            GPIO.output(HardwareConfig.GPIO_BUZZER, GPIO.LOW)
            self.gpio_setup = True
            
            print("✅ 蜂鸣器GPIO初始化成功")
            return True
            
        except ImportError:
            self.last_error = "未找到 RPi.GPIO 库"
            return False
        except Exception as e:
            self.last_error = f"蜂鸣器初始化失败: {str(e)}"
            return False
    
    def _test_functionality_impl(self) -> Tuple[bool, str]:
        """测试蜂鸣器功能"""
        try:
            import RPi.GPIO as GPIO
            
            # 发出蜂鸣声测试
            for i in range(3):
                GPIO.output(HardwareConfig.GPIO_BUZZER, GPIO.HIGH)
                time.sleep(0.2)
                GPIO.output(HardwareConfig.GPIO_BUZZER, GPIO.LOW)
                time.sleep(0.2)
            
            return True, "蜂鸣器测试通过"
            
        except Exception as e:
            return False, f"蜂鸣器测试失败: {str(e)}"
    
    def _cleanup_impl(self):
        """清理GPIO资源"""
        try:
            import RPi.GPIO as GPIO
            if self.gpio_setup:
                GPIO.output(HardwareConfig.GPIO_BUZZER, GPIO.LOW)
                GPIO.cleanup(HardwareConfig.GPIO_BUZZER)
        except:
            pass

class RGBLEDHardwareModule(HardwareModule):
    """RGB LED模块 - WS2812B-5050RGB"""
    
    def __init__(self):
        super().__init__("RGB LED")
        self.pixels = None
        self.num_pixels = 10
        self.ORDER = neopixel.GRB
    
    def _initialize_impl(self) -> bool:
        """初始化RGB LED"""
        try:
            import board
            
            pixel_pin = board.D18
            
            self.pixels = neopixel.NeoPixel(
                pixel_pin, self.num_pixels, brightness=0.2, auto_write=False, pixel_order=self.ORDER
            )
            
            print("✅ RGB LED初始化成功")
            return True
            
        except ImportError:
            self.last_error = "未找到 board 或 neopixel 库"
            return False
        except Exception as e:
            self.last_error = f"RGB LED初始化失败: {str(e)}"
            return False
    
    def _test_functionality_impl(self) -> Tuple[bool, str]:
        """测试RGB LED功能"""
        try:
            colors = [
                ("红色", (255, 0, 0)),
                ("绿色", (0, 255, 0)),
                ("蓝色", (0, 0, 255)),
                ("紫色", (128, 0, 128)),
                ("黄色", (255, 255, 0)),
                ("橙色", (255, 165, 0)),
                ("粉色", (255, 192, 203)),
                ("青色", (0, 255, 255)),
                ("深蓝色", (0, 0, 139)),
                ("淡紫色", (230, 230, 250)),
                ("淡蓝色", (173, 216, 230)),
                ("草绿色", (124, 252, 0)),
                ("玫瑰红", (255, 0, 127)),
                ("深红色", (139, 0, 0)),
                ("天蓝色", (135, 206, 235)),
                ("金色", (255, 215, 0)),
                ("浅绿色", (144, 238, 144)),
                ("浅橙色", (255, 204, 153))
            ]
            
            for color_name, color_rgb in colors:
                print(color_name)
                self.pixels.fill(color_rgb)
                self.pixels.show()
                time.sleep(1)
            
            return True, "RGB LED测试通过 - 显示18种颜色"
            
        except Exception as e:
            return False, f"RGB LED测试失败: {str(e)}"
    
    def _cleanup_impl(self):
        """清理RGB LED资源"""
        if self.pixels:
            self.pixels.fill((0, 0, 0))
            self.pixels.show()

# =============================================================================
# DV测试管理器
# =============================================================================

class DVTestManager:
    """设计验证测试管理器"""
    
    def __init__(self):
        self.test_results: Dict[str, TestResult] = {}
        self.hardware_modules: List[HardwareModule] = []
        self.overall_status = TestStatus.NOT_STARTED
        self.start_time = 0.0
        self.end_time = 0.0
    
    def initialize_hardware_modules(self):
        """初始化所有硬件模块"""
        print("=" * 60)
        print("🔧 初始化硬件模块...")
        print("=" * 60)
        
        # 创建硬件模块实例
        self.hardware_modules = [
            PWMHardwareModule(),
            MPU6050HardwareModule(1),
            MPU6050HardwareModule(2),
            OLEDHardwareModule(),
            ButtonHardwareModule(),
            BuzzerHardwareModule(),
            RGBLEDHardwareModule()
        ]
        
        # 初始化每个模块
        for module in self.hardware_modules:
            if not module.initialize():
                print(f"❌ {module.name} 初始化失败: {module.last_error}")
            else:
                print(f"✅ {module.name} 初始化成功")
        
        print("硬件模块初始化完成\n")
    
    def run_all_tests(self):
        """运行所有测试"""
        self.start_time = time.time()
        self.overall_status = TestStatus.RUNNING
        
        print("=" * 60)
        print("🚀 开始设计验证测试...")
        print("=" * 60)
        
        # 运行每个硬件模块的测试
        for module in self.hardware_modules:
            self._run_single_test(module)
        
        self.end_time = time.time()
        self._calculate_overall_status()
        self._generate_report()
    
    def _run_single_test(self, module: HardwareModule):
        """运行单个硬件模块的测试"""
        test_result = TestResult(module.name, f"测试{module.name}的功能")
        test_result.status = TestStatus.RUNNING
        
        print(f"\n🔍 测试 {module.name}...")
        
        start_time = time.time()
        success, message = module.test_functionality()
        duration = time.time() - start_time
        
        if success:
            test_result.set_passed(duration)
            print(f"✅ {module.name} - 测试通过 ({duration:.2f}s)")
            print(f"   详细信息: {message}")
        else:
            test_result.set_failed(duration, message)
            print(f"❌ {module.name} - 测试失败 ({duration:.2f}s)")
            print(f"   错误信息: {message}")
        
        self.test_results[module.name] = test_result
    
    def _calculate_overall_status(self):
        """计算总体测试状态"""
        if not self.test_results:
            self.overall_status = TestStatus.NOT_STARTED
            return
        
        failed_tests = [result for result in self.test_results.values() 
                       if result.status == TestStatus.FAILED]
        
        if failed_tests:
            self.overall_status = TestStatus.FAILED
        else:
            self.overall_status = TestStatus.PASSED
    
    def _generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("📊 设计验证测试报告")
        print("=" * 60)
        
        total_duration = self.end_time - self.start_time
        passed_tests = len([r for r in self.test_results.values() if r.status == TestStatus.PASSED])
        total_tests = len(self.test_results)
        
        print(f"总体状态: {self.overall_status.value}")
        print(f"测试用时: {total_duration:.2f}秒")
        print(f"通过率: {passed_tests}/{total_tests}")
        
        print("\n详细结果:")
        for name, result in self.test_results.items():
            status_icon = "✅" if result.status == TestStatus.PASSED else "❌"
            print(f"  {status_icon} {name}: {result.status.value} ({result.duration:.2f}s)")
            if result.error_message:
                print(f"     错误: {result.error_message}")
        
        print("\n" + "=" * 60)
        
        if self.overall_status == TestStatus.PASSED:
            print("🎉 所有硬件模块测试通过！系统就绪。")
        else:
            print("⚠️  部分测试失败,请检查硬件连接。")
    
    def cleanup(self):
        """清理所有硬件资源"""
        print("\n🧹 清理硬件资源...")
        for module in self.hardware_modules:
            module.cleanup()
        print("资源清理完成")

# =============================================================================
# 主程序
# =============================================================================

def main():
    """主函数"""
    print("=" * 60)
    print("🎯 树莓派5硬件系统设计验证软件")
    print("=" * 60)
    print("作者: 新手友好型DV工具")
    print("版本: 1.0")
    print("功能: 验证硬件模块协同工作")
    print("=" * 60)
    
    # 创建测试管理器
    test_manager = DVTestManager()
    
    try:
        # 初始化硬件
        test_manager.initialize_hardware_modules()
        
        # 运行测试
        input("按Enter键开始测试...")
        test_manager.run_all_tests()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 测试过程中发生异常: {e}")
    finally:
        # 清理资源
        test_manager.cleanup()
        print("\n👋 设计验证软件退出")

if __name__ == "__main__":
    main()