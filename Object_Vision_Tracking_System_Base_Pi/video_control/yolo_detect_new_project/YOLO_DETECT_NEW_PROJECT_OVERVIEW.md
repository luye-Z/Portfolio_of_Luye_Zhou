# YOLO 目标检测与跟踪系统项目综述与使用手册

## 项目简介

本项目是一个基于树莓派的实时目标检测与跟踪系统，采用 YOLO（You Only Look Once）深度学习模型进行目标检测，并结合 PID 控制算法、卡尔曼滤波和前馈控制实现精准的伺服舵机跟踪。系统通过摄像头捕获视频流，利用 YOLO 模型检测特定目标（如无人机），计算目标中心坐标，并通过舵机控制系统实时调整云台角度，使目标始终保持在画面中心。

系统支持多种运行模式，包括基础 YOLO 检测模式、卡尔曼滤波平滑模式、PID 参数调整模式、数据记录模式等，用户可通过物理按键切换模式，OLED 屏幕实时显示当前模式。

## 硬件要求

- **树莓派 4B/5**（推荐 4GB 内存以上）
- **树莓派摄像头模块**（CSI 接口）
- **双轴舵机云台**（支持 PWM 控制）
- **激光测距传感器**（VL53L0X）
- **OLED 显示屏**（SSD1306，I2C 接口）
- **RGB LED**（WS2812B）
- **蜂鸣器**（有源）
- **物理按键**
- **MPU6050 陀螺仪**（可选）
- **电源模块**（为树莓派和外设供电）

## 软件依赖

### Python 包依赖
- **OpenCV** (`opencv-python`)
- **Ultralytics YOLO** (`ultralytics`)
- **Picamera2** (`picamera2`)
- **RPi.GPIO**
- **smbus2**
- **rpi-hardware-pwm**
- **luma.oled**
- **neopixel**
- **numpy**

### 系统依赖
- **Raspberry Pi OS**（64位推荐）
- **启用 I2C、PWM 接口**
- **配置摄像头模块**

安装命令示例：
```bash
sudo apt update
sudo apt install python3-pip python3-opencv
pip3 install ultralytics picamera2 RPi.GPIO smbus2 rpi-hardware-pwm luma.oled neopixel numpy
```

## 项目结构

```
yolo_detect_new_project/
├── main.py                    # 主程序（基础版本）
├── main_test.py               # 主程序（增强版本，支持多模式）
├── system_manager.py          # 系统管理器，整合所有硬件驱动
├── yolo_predict.py            # YOLO 检测器类
├── core_algorithm/            # 核心算法模块
│   ├── PID_controller.py      # PID 控制器
│   ├── kalman_algorithm.py    # 卡尔曼滤波器
│   └── smart_control_algorithm.py  # 智能控制算法（前馈）
├── core_hardware_driver/      # 硬件驱动模块
│   ├── pwm_servos_control.py  # 舵机控制器
│   ├── buzzer_driver.py       # 蜂鸣器控制器
│   ├── vl53l0x_drive_threat.py # 激光测距传感器线程驱动
│   ├── oled_driver.py         # OLED 显示屏驱动
│   ├── rgb_led_control.py     # RGB LED 控制
│   ├── button_driver.py       # 物理按键驱动
│   └── mpu6050_driver.py      # MPU6050 驱动（可选）
├── detection_records_analyse/ # 数据记录与分析工具
│   ├── detection_records_analyse.py
│   └── detection_records_analyse_new.py
├── reference_code_filefolder/ # 参考代码
├── software_manual/           # 软件文档
└── scripts_record.md          # 脚本记录
```

## 核心模块说明

### 1. YOLODetector (`yolo_predict.py`)
负责摄像头初始化和 YOLO 模型推理。
- 使用 `Picamera2` 捕获视频流
- 加载 Ultralytics YOLO 模型（NCNN 格式）
- 检测目标并过滤过大框体
- 提供目标中心坐标接口

### 2. SystemManager (`system_manager.py`)
系统的中枢管理器，负责：
- 初始化所有硬件驱动（舵机、传感器、LED、蜂鸣器、OLED、按键）
- 管理程序运行模式（菜单模式、多种检测模式）
- 处理按键事件（短按、长按、双击）
- OLED 显示更新（独立线程，避免阻塞主循环）
- 资源清理（上下文管理器确保安全退出）

### 3. PIDController (`core_algorithm/PID_controller.py`)
实现 PD 控制算法（比例-微分），用于舵机跟踪。
- 根据目标位置与画面中心的误差计算舵机角度
- 支持死区过滤，避免微小抖动
- 提供前馈控制接口，增强动态响应
- 可实时调整 PID 参数

### 4. Kalman2DTracker (`core_algorithm/kalman_algorithm.py`)
二维卡尔曼滤波器，用于平滑目标轨迹并预测短暂丢失的目标位置。
- 基于匀速运动模型
- 在目标丢失时提供短期预测
- 减少 YOLO 检测噪声带来的抖动

### 5. SmartControlAlgorithm (`core_algorithm/smart_control_algorithm.py`)
简单线性外推算法，根据目标历史位置预测下一帧位置，实现超前控制。

### 6. 硬件驱动模块 (`core_hardware_driver/`)
- **ServoController**: 通过硬件 PWM 控制双轴舵机，提供角度设置接口
- **BuzzerController**: 线程化蜂鸣器控制，支持滴滴报警声
- **VL53L0X_Threaded**: 线程化激光测距，持续更新距离数据
- **OLEDDriver**: SSD1306 OLED 显示文本
- **LEDController**: 控制 RGB LED 颜色
- **ButtonDriver**: 检测物理按键事件（短按、长按、双击）

## 运行模式详解

系统支持以下程序模式（通过按键切换）：

| 模式索引 | 模式名称（OLED 显示） | 描述 |
|----------|----------------------|------|
| 0 | `program menu` | 菜单模式，选择其他模式 |
| 1 | `PID_parameter\nadjust` | PID 参数调整模式，终端输入 PID 参数 |
| 2 | `Kalman_test` | 卡尔曼滤波测试模式，开启卡尔曼滤波 |
| 3 | `yolo detection\nvc show` | YOLO 检测 + 视频显示模式 |
| 4 | `yolo detection\nvc show\nmake datasets` | YOLO 检测 + 视频显示 + 数据集制作 |
| 5 | `yolo detection\nno image` | YOLO 检测模式，无视频显示（默认） |
| 6 | `yolo detection\nno buzzer` | YOLO 检测，无蜂鸣器 |
| 7 | `yolo detection\nno image no buzzer` | YOLO 检测，无显示无蜂鸣器 |
| 8 | `yolo detection\nfeedforward_control` | 前馈控制测试模式 |
| 9 | `draw_record_chart\nOnly_PID` | 数据记录模式（仅 PID） |
| 10 | `draw_record_chart\nkalman` | 数据记录模式（卡尔曼） |
| 11 | `draw_record_chart\nfeedforward_control` | 数据记录模式（前馈控制） |

### 按键操作说明
- **短按**（在菜单模式下）：切换选择下一个模式
- **双击**（在菜单模式下）：进入选中的模式
- **长按**（在任何运行模式下）：返回菜单模式，并重置所有外设状态

## 使用方法

### 1. 系统启动
```bash
cd /home/pi/projects/yolo26/video_control/yolo_detect_new_project
python3 main_test.py
```

### 2. 模式切换流程
1. 系统启动后自动进入菜单模式（OLED 显示 `--- MENU ---` 和当前选中的模式）
2. 短按按键切换选择模式（OLED 实时更新）
3. 双击按键进入选中的运行模式
4. 在运行模式下，系统开始目标检测与跟踪
5. 长按按键返回菜单模式

### 3. 基础 YOLO 检测模式（默认）
- 摄像头实时捕获画面
- YOLO 模型检测目标（无人机等）
- 舵机自动跟踪目标，保持目标在画面中心
- 蜂鸣器在检测到目标时报警，RGB LED 变红色
- 未检测到目标时蜂鸣器停止，LED 变绿色
- 激光测距传感器实时测量目标距离并输出到终端

### 4. PID 参数调整模式
进入此模式后，终端会提示输入 PID 参数：
```
请输入 kp_pan (默认: 0.35):
请输入 kp_tilt (默认: 0.35):
请输入 kd_pan (默认: 0.08):
请输入 kd_tilt (默认: 0.08):
```
输入参数后按回车开始运行，系统将使用新参数进行控制。

### 5. 数据记录模式
系统将每一帧的目标坐标、误差、PID 输出等数据记录到 CSV 文件，保存在 `detection_records_analyse/detection_records/` 目录下，文件名包含时间戳。可用于后续分析与图表绘制。

### 6. 卡尔曼滤波模式
启用卡尔曼滤波器平滑目标轨迹，在目标短暂丢失时（如遮挡）提供预测位置，提高跟踪稳定性。

### 7. 前馈控制模式
在前馈控制基础上增加对目标速度的预测，进一步提高动态响应性能。

## 配置与调参

### 模型路径配置
在 `system_manager.py` 第 22 行修改 `MODEL_PATH` 指向你的 YOLO 模型文件：
```python
MODEL_PATH = "/home/pi/projects/yolo26/model_folder/ncnn_format_model/640_imgsz_ncnn_model/yolo26n_quadcopter_0405_ncnn_model"
```

### 屏幕分辨率
默认分辨率 864×640，在 `yolo_predict.py` 中修改 `SCREEN_WIDTH` 和 `SCREEN_HEIGHT`。

### PID 参数调参
- **kp_pan, kp_tilt**: 比例系数，影响响应速度，过大易振荡
- **kd_pan, kd_tilt**: 微分系数，抑制超调，提高稳定性
- **dead_zone**: 死区像素数，小于该值的误差不响应，避免抖动

建议通过 PID 参数调整模式在线调试。

### 卡尔曼滤波器参数
在 `kalman_algorithm.py` 中调整：
- `processNoiseCov`: 过程噪声协方差，值越大对模型信任越低
- `measurementNoiseCov`: 测量噪声协方差，值越大对 YOLO 检测信任越低

### 按键参数
在 `button_driver.py` 中调整：
- `double_click_window`: 双击检测时间窗口（秒）
- `long_press_threshold`: 长按判定阈值（秒）
- `bouncetime`: 硬件消抖时间（毫秒）

## 故障排除

### 1. 摄像头无法打开
- 检查摄像头连接和启用状态：`sudo raspi-config` → `Interface Options` → `Camera`
- 确保 `picamera2` 已安装

### 2. I2C 设备无法通信（OLED、激光测距）
- 启用 I2C：`sudo raspi-config` → `Interface Options` → `I2C`
- 检查设备地址：`sudo i2cdetect -y 1`
- 确认接线正确（SDA、SCL、VCC、GND）

### 3. PWM 舵机无反应
- 确认使用硬件 PWM 引脚（GPIO 12/13 或 18/19）
- 检查电源供应，舵机需独立供电
- 确认 `rpi-hardware-pwm` 安装

### 4. YOLO 模型加载失败
- 检查模型文件路径是否存在
- 确认模型格式为 Ultralytics 支持的格式（`.pt` 或 NCNN 格式）
- 确保有足够的 RAM 和 Swap 空间

### 5. 性能问题（帧率低）
- 关闭视频显示可大幅提升帧率
- 降低 YOLO 模型输入分辨率（`imgsz` 参数）
- 使用轻量级模型（如 YOLOv8n）
- 确保树莓派散热良好，避免降频

## 附录

### 文件说明表
| 文件 | 功能 |
|------|------|
| `main.py` | 基础版本，简单 YOLO 检测与舵机跟踪 |
| `main_test.py` | 增强版本，支持多模式切换，推荐使用 |
| `system_manager.py` | 系统管理器，硬件整合与模式管理 |
| `yolo_predict.py` | YOLO 检测器类 |
| `core_algorithm/PID_controller.py` | PID 控制器 |
| `core_algorithm/kalman_algorithm.py` | 卡尔曼滤波器 |
| `core_algorithm/smart_control_algorithm.py` | 前馈控制算法 |
| `core_hardware_driver/` 下各文件 | 硬件驱动 |

### 硬件接线参考
| 设备 | 树莓派引脚 | 备注 |
|------|------------|------|
| 摄像头 | CSI 接口 | 专用接口 |
| 舵机（水平） | GPIO 12（PWM0） | 硬件 PWM |
| 舵机（垂直） | GPIO 13（PWM1） | 硬件 PWM |
| 激光测距 VL53L0X | SDA: GPIO2, SCL: GPIO3 | I2C |
| OLED SSD1306 | SDA: GPIO2, SCL: GPIO3 | I2C（可共用） |
| RGB LED WS2812B | GPIO 18 | 需串联 330Ω 电阻 |
| 蜂鸣器 | GPIO 25 | 有源，低电平触发 |
| 按键 | GPIO 23 | 上拉电阻 |

### 常用命令
```bash
# 查看系统资源
htop

# 监控温度
vcgencmd measure_temp

# 检查 I2C 设备
sudo i2cdetect -y 1

# 测试摄像头
libcamera-hello

# 测试舵机
python3 -c "from core_hardware_driver.pwm_servos_control import ServoController; s=ServoController(); s.set_pan_angle(0); s.set_tilt_angle(90); s.cleanup()"
```

## 更新日志
- **2026-04-06**: 项目综述文档创建
- **2026-03-29**: `yolo_predict.py` 优化性能，减少内存拷贝
- **2026-03-28**: 增加前馈控制算法
- **2026-02-17**: 基础版本完成，支持 YOLO 检测与 PID 跟踪

## 联系与贡献
项目维护者：luye
如有问题或建议，请提交 Issue 或 Pull Request。

---

*文档最后更新：2026年4月6日*