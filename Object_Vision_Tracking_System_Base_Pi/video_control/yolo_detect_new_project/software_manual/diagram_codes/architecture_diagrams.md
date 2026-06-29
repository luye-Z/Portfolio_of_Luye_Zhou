# YOLO 检测与跟踪系统架构图

## 1. 类图 (Class Diagram)

```mermaid
classDiagram
    class SystemManager {
        -buzzer: BuzzerController
        -oled: OLEDDriver
        -laser_sensor: VL53L0X_Threaded
        -detector: YOLODetector
        -servo_controller: ServoController
        -rgb_led: LEDController
        -button_driver: ButtonDriver
        -mpu6050: MPU6050driver
        -program_mode_storage: tuple
        -menu_select_idx: int
        -current_program_mode: str
        -oled_update_queue: Queue
        +__init__()
        +__enter__()
        +__exit__()
        -_oled_update_worker()
        +program_mode_manager_oled_show()
        +action_short_press()
        +action_long_press()
        +action_double_click()
        +get_program_mode()
        +program_mode_set()
    }

    class YOLODetector {
        -picam2: Picamera2
        -model: YOLO
        -SCREEN_WIDTH: int
        -SCREEN_HEIGHT: int
        -target_detected: bool
        -target_center_x: float
        -target_center_y: float
        -yolo_detect_turn: bool
        -smart_last_target_center_x: float
        -smart_last_target_center_y: float
        -smart_now_target_center_x: float
        -smart_now_target_center_y: float
        +__init__(model_path, imgsz, conf)
        +start()
        +stop()
        +cleanup()
        +detect_frame() -> (result, frame)
        +get_target_detected() -> bool
        +get_target_center() -> (float, float)
        +update_smart_control_params()
        +reverse_yolo_detect_turn()
        +calculate_smart_control_target_center() -> (float, float)
    }

    class ServoController {
        -servo_pan: HardwarePWM
        -servo_tilt: HardwarePWM
        -SERVO_MIN: int
        -SERVO_MAX: int
        -DEG_PER_PIX: float
        -kp_pan: float
        -kp_tilt: float
        -dead_zone: int
        -current_pan: float
        -current_tilt: float
        +__init__(pan_chan, tilt_chan, chip_id, kp_pan, kp_tilt)
        -_set_angle(pwm_obj, angle)
        +track_target(target_x, target_y, screen_w, screen_h)
        +reset()
        +stop()
        +cleanup()
    }

    class BuzzerController {
        -buzzer_pin: int
        -_active_event: threading.Event
        -_stop_event: threading.Event
        -_thread: threading.Thread
        +__init__(pin)
        -_handler()
        +start_alarm()
        +stop_alarm()
        +cleanup()
    }

    class OLEDDriver {
        -serial: i2c
        -device: ssd1306
        -font: ImageFont
        +__init__(port, address, width, height)
        +show_text(text, size, x, y)
        +cleanup()
    }

    class LEDController {
        -pixel: neopixel.NeoPixel
        -colors: dict
        +__init__(pin, brightness)
        +set_color_rgb(r, g, b)
        +set_color_name(color_name)
        +off()
        +cleanup()
    }

    class VL53L0X_Threaded {
        -address: int
        -bus: SMBus
        -_distance: int
        -_running: bool
        +__init__(address, bus_id)
        -_setup()
        -_update()
        +start()
        +stop()
        +cleanup()
        +distance: property
    }

    class MPU6050driver {
        -sensor: mpu6050
        -alpha: float
        -offsets: dict
        -pitch: float
        -roll: float
        -last_time: float
        -lock: threading.Lock
        +__init__(address, alpha)
        +calibrate(samples)
        +get_pose() -> (float, float)
        +start_reading()
        +get_mpu6050_angle_pose() -> (float, float)
        +cleanup()
    }

    class ButtonDriver {
        -pin: int
        -short_cb: function
        -long_cb: function
        -double_cb: function
        -last_press_time: float
        -last_release_time: float
        -timer: Timer
        +__init__(pin, short_cb, long_cb, double_cb)
        -_handle_event(channel)
        -_trigger_short()
        -_safe_call(callback)
        +cleanup()
    }

    SystemManager --> YOLODetector : 包含
    SystemManager --> ServoController : 包含
    SystemManager --> BuzzerController : 包含
    SystemManager --> OLEDDriver : 包含
    SystemManager --> LEDController : 包含
    SystemManager --> VL53L0X_Threaded : 包含
    SystemManager --> MPU6050driver : 包含
    SystemManager --> ButtonDriver : 包含
    YOLODetector ..> Picamera2 : 使用
    YOLODetector ..> YOLO : 使用
    ServoController ..> HardwarePWM : 使用
    OLEDDriver ..> ssd1306 : 使用
    LEDController ..> neopixel : 使用
    VL53L0X_Threaded ..> SMBus : 使用
    MPU6050driver ..> mpu6050 : 使用
    ButtonDriver ..> GPIO : 使用
```

## 2. 系统流程图 (System Flowchart)

```mermaid
flowchart TD
    A[系统启动] --> B[初始化 SystemManager]
    B --> C[启动相机和传感器]
    C --> D{进入主循环}
    
    D --> E{检测模式判断}
    E -->|YOLO 检测模式| F[调用 detect_frame]
    F --> G[更新智能控制参数]
    G --> H[翻转检测模式标志]
    
    E -->|智能控制模式| I[计算预测目标位置]
    I --> J[翻转检测模式标志]
    
    H --> K{是否检测到目标?}
    J --> K
    
    K -->|是| L[控制舵机跟踪目标]
    L --> M[启动蜂鸣器报警]
    M --> N[RGB LED 显示红色]
    
    K -->|否| O[停止蜂鸣器报警]
    O --> P[RGB LED 显示绿色]
    
    N --> Q[显示图像]
    P --> Q
    
    Q --> R{是否按下'q'键?}
    R -->|是| S[清理资源并退出]
    R -->|否| D
    
    S --> T[系统关闭]
```

## 3. 硬件组件图 (Hardware Component Diagram)

```mermaid
graph TB
    subgraph "树莓派 4B"
        subgraph "软件模块"
            SM[SystemManager]
            YD[YOLO Detector]
            SC[Servo Controller]
            BC[Buzzer Controller]
            OD[OLED Driver]
            LC[LED Controller]
            VS[VL53L0X Sensor]
            MP[MPU6050 Driver]
            BD[Button Driver]
        end
        
        subgraph "硬件接口"
            I2C[I2C 总线]
            PWM[PWM 输出]
            GPIO[GPIO 引脚]
            CSI[CSI 摄像头接口]
        end
    end
    
    subgraph "外部硬件"
        CAM[树莓派摄像头]
        PAN[水平舵机]
        TILT[垂直舵机]
        BUZ[蜂鸣器]
        OLED[OLED 显示屏]
        LED[RGB LED]
        LASER[VL53L0X 激光测距]
        IMU[MPU6050 姿态传感器]
        BTN[按键]
    end
    
    CAM -- CSI --> YD
    PAN -- PWM --> SC
    TILT -- PWM --> SC
    BUZ -- GPIO --> BC
    OLED -- I2C --> OD
    LED -- GPIO --> LC
    LASER -- I2C --> VS
    IMU -- I2C --> MP
    BTN -- GPIO --> BD
    
    SM --> YD
    SM --> SC
    SM --> BC
    SM --> OD
    SM --> LC
    SM --> VS
    SM --> MP
    SM --> BD
```

## 4. 数据流图 (Data Flow Diagram)

```mermaid
flowchart LR
    subgraph "输入"
        CAM[摄像头图像]
        BTN[按键事件]
        LASER[激光测距]
        IMU[姿态数据]
    end
    
    subgraph "处理"
        YD[YOLO 检测]
        SC[舵机控制]
        SM[系统管理]
    end
    
    subgraph "输出"
        PAN[水平舵机]
        TILT[垂直舵机]
        BUZ[蜂鸣器]
        OLED[OLED 显示]
        LED[RGB LED]
        DIS[屏幕显示]
    end
    
    CAM --> YD
    YD --> SM
    BTN --> SM
    LASER --> SM
    IMU --> SM
    
    SM --> SC
    SM --> BUZ
    SM --> OLED
    SM --> LED
    SM --> DIS
    
    SC --> PAN
    SC --> TILT
```

## 5. 状态图 (State Diagram - 程序模式)

```mermaid
stateDiagram-v2
    [*] --> MenuMode
    MenuMode --> DetectionWithDisplay : 双击选择模式1
    MenuMode --> HeadlessMode : 双击选择模式2
    MenuMode --> DetectionNoBuzzer : 双击选择模式3
    MenuMode --> HeadlessNoBuzzer : 双击选择模式4
    MenuMode --> DrawCharts : 双击选择模式5
    
    DetectionWithDisplay --> MenuMode : 长按返回
    HeadlessMode --> MenuMode : 长按返回
    DetectionNoBuzzer --> MenuMode : 长按返回
    HeadlessNoBuzzer --> MenuMode : 长按返回
    DrawCharts --> MenuMode : 长按返回
    
    state DetectionWithDisplay {
        [*] --> YOLODetection
        YOLODetection --> SmartControl : 切换标志
        SmartControl --> YOLODetection : 切换标志
    }
    
    state HeadlessMode {
        [*] --> YOLODetectionNoDisplay
        YOLODetectionNoDisplay --> SmartControlNoDisplay
        SmartControlNoDisplay --> YOLODetectionNoDisplay
    }
```

## 6. 时序图 (Sequence Diagram - 主循环)

```mermaid
sequenceDiagram
    participant M as Main
    participant SM as SystemManager
    participant YD as YOLODetector
    participant SC as ServoController
    participant BC as BuzzerController
    participant LC as LEDController
    
    M->>SM: 初始化
    SM->>YD: 启动相机
    SM->>其他硬件: 启动传感器
    
    loop 主循环
        M->>YD: 获取检测模式
        alt YOLO检测模式
            YD->>YD: detect_frame()
            YD->>YD: 更新智能控制参数
            YD->>YD: 翻转检测模式标志
            YD->>M: 返回检测结果
            M->>SC: 跟踪目标(如果检测到)
            M->>BC: 控制蜂鸣器
            M->>LC: 控制LED
        else 智能控制模式
            YD->>YD: 计算预测目标位置
            YD->>YD: 翻转检测模式标志
            YD->>M: 返回预测位置
            M->>SC: 跟踪预测目标
        end
        M->>M: 显示图像
        M->>M: 检查退出键
    end
    
    M->>SM: 清理资源
    SM->>所有硬件: 关闭
```

## 总结

该系统是一个完整的嵌入式计算机视觉项目，具有以下特点：

1. **模块化设计**：每个硬件驱动独立封装，便于维护和测试。
2. **智能控制**：交替使用 YOLO 检测和预测控制，平衡精度和性能。
3. **多模式支持**：通过按键切换不同工作模式，适应不同场景。
4. **资源管理**：使用上下文管理器和清理函数确保资源正确释放。
5. **实时反馈**：通过蜂鸣器、LED 和 OLED 提供多感官反馈。

该架构适用于需要实时目标检测和跟踪的嵌入式应用，如无人机跟踪、安防监控、机器人视觉等。