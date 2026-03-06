#!/usr/bin/env python3
"""
PID控制器测试脚本
测试水平方向使用减号（镜像调整）的影响
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PID_controller import PIDController

def test_pid_controller():
    """测试PID控制器的基本功能"""
    print("=== PID控制器测试 ===\n")
    
    # 初始化PID控制器，使用默认参数
    pid = PIDController(kp_pan=0.1, kp_tilt=0.1, kd_pan=0.05, kd_tilt=0.05)
    
    # 模拟屏幕尺寸
    screen_w = 640
    screen_h = 480
    
    print(f"屏幕尺寸: {screen_w}x{screen_h}")
    print(f"初始角度: pan={pid.current_pan:.2f}°, tilt={pid.current_tilt:.2f}°")
    print(f"死区: {pid.dead_zone} 像素")
    print()
    
    # 测试用例1: 目标在屏幕中心右侧（error_x > 0）
    print("--- 测试1: 目标在屏幕中心右侧 ---")
    target_x = screen_w / 2 + 50  # 右侧50像素
    target_y = screen_h / 2       # 中心垂直位置
    print(f"目标位置: ({target_x:.1f}, {target_y:.1f})")
    
    error_x = target_x - (screen_w / 2)
    error_y = target_y - (screen_h / 2)
    print(f"误差: error_x={error_x:.1f}, error_y={error_y:.1f}")
    
    # 保存初始角度
    pan_before = pid.current_pan
    tilt_before = pid.current_tilt
    
    # 执行PID计算
    pid.pid_control_calculate(target_x, target_y, screen_w, screen_h)
    
    # 获取结果
    pan_after, tilt_after = pid.get_PID_controller_output()
    
    print(f"计算前角度: pan={pan_before:.2f}°, tilt={tilt_before:.2f}°")
    print(f"计算后角度: pan={pan_after:.2f}°, tilt={tilt_after:.2f}°")
    print(f"角度变化: Δpan={pan_after - pan_before:.2f}°, Δtilt={tilt_after - tilt_before:.2f}°")
    
    # 分析水平方向
    if error_x > 0:
        delta_pan = pan_after - pan_before
        if delta_pan < 0:
            print("✓ 水平方向: error_x>0 导致 pan 减小（使用减号），符合镜像调整")
        else:
            print("✗ 水平方向: error_x>0 但 pan 增加，与预期不符")
    print()
    
    # 测试用例2: 目标在屏幕中心左侧（error_x < 0）
    print("--- 测试2: 目标在屏幕中心左侧 ---")
    pid2 = PIDController(kp_pan=0.1, kp_tilt=0.1, kd_pan=0.05, kd_tilt=0.05)
    target_x = screen_w / 2 - 50  # 左侧50像素
    target_y = screen_h / 2
    print(f"目标位置: ({target_x:.1f}, {target_y:.1f})")
    
    error_x = target_x - (screen_w / 2)
    pan_before = pid2.current_pan
    pid2.pid_control_calculate(target_x, target_y, screen_w, screen_h)
    pan_after, _ = pid2.get_PID_controller_output()
    
    print(f"误差: error_x={error_x:.1f}")
    print(f"角度变化: Δpan={pan_after - pan_before:.2f}°")
    
    if error_x < 0:
        delta_pan = pan_after - pan_before
        if delta_pan > 0:
            print("✓ 水平方向: error_x<0 导致 pan 增加（使用减号），符合镜像调整")
        else:
            print("✗ 水平方向: error_x<0 但 pan 减小，与预期不符")
    print()
    
    # 测试用例3: 目标在屏幕中心下方（error_y > 0）
    print("--- 测试3: 目标在屏幕中心下方 ---")
    pid3 = PIDController(kp_pan=0.1, kp_tilt=0.1, kd_pan=0.05, kd_tilt=0.05)
    target_x = screen_w / 2
    target_y = screen_h / 2 + 40  # 下方40像素
    print(f"目标位置: ({target_x:.1f}, {target_y:.1f})")
    
    error_y = target_y - (screen_h / 2)
    tilt_before = pid3.current_tilt
    pid3.pid_control_calculate(target_x, target_y, screen_w, screen_h)
    _, tilt_after = pid3.get_PID_controller_output()
    
    print(f"误差: error_y={error_y:.1f}")
    print(f"角度变化: Δtilt={tilt_after - tilt_before:.2f}°")
    
    if error_y > 0:
        delta_tilt = tilt_after - tilt_before
        if delta_tilt > 0:
            print("✓ 垂直方向: error_y>0 导致 tilt 增加（使用加号）")
        else:
            print("✗ 垂直方向: error_y>0 但 tilt 减小，与预期不符")
    print()
    
    # 测试用例4: 多次迭代，观察收敛
    print("--- 测试4: 多次迭代（模拟追踪过程） ---")
    pid4 = PIDController(kp_pan=0.1, kp_tilt=0.1, kd_pan=0.05, kd_tilt=0.05)
    target_x = screen_w / 2 + 100  # 右侧100像素
    target_y = screen_h / 2 + 80   # 下方80像素
    
    print(f"目标位置: ({target_x:.1f}, {target_y:.1f})")
    print("迭代  |  pan角度  |  tilt角度  |  error_x  |  error_y")
    print("-" * 55)
    
    for i in range(5):
        error_x = target_x - (screen_w / 2)
        error_y = target_y - (screen_h / 2)
        pan, tilt = pid4.get_PID_controller_output()
        print(f"{i+1:4d}  |  {pan:7.2f}°  |  {tilt:7.2f}°  |  {error_x:7.1f}  |  {error_y:7.1f}")
        pid4.pid_control_calculate(target_x, target_y, screen_w, screen_h)
        # 模拟目标移动（逐渐向中心靠拢）
        target_x = target_x * 0.8 + (screen_w / 2) * 0.2
        target_y = target_y * 0.8 + (screen_h / 2) * 0.2
    
    print()
    
    # 总结
    print("=== 测试总结 ===")
    print("1. 水平方向使用减号（self.current_pan -= delta_pan）是为了镜像调整。")
    print("2. 当目标在右侧（error_x>0）时，pan角度减小，舵机向左转，补偿镜像效应。")
    print("3. 垂直方向使用加号（self.current_tilt += delta_tilt），但注释说应用减法，可能存在不一致。")
    print("4. 测试完成，可以运行此脚本验证PID控制器行为。")

if __name__ == "__main__":
    test_pid_controller()