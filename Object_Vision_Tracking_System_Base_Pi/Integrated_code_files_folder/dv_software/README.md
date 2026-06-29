# 主控：树莓派5 (raspberrypi 5)

# GPIO 连接信息
## 1.舵机控制电路
GPIO12_PWM0 控制舵机1
GPIO13_PWM1 控制舵机2
## 2.按键电路
按键消除抖动电路，微动开关薄膜按钮，按钮一端接GPIO23
按键按下闭合，GPIO23 接 +3.3V ,按钮松开，GPIO23 接 GND

## 3. MPU6050 驱动电路
MPU6050_1 连接到 I2C 总线上， MPU6050的SLC 接到 树莓派5的GPIO3_SCL上
MPU6050_1的SDA 接到 树莓派5的GPIO2_SDA上，ADO接GND，INT接 树莓派 的GPIO7

MPU6050_2 也连接到 I2C 总线上， MPU6050的SLC 接到 树莓派5的GPIO3_SCL上
MPU6050_2的SDA 接到 树莓派5的GPIO2_SDA上，ADO接+3.3V，INT接 树莓派 的GPIO24

## 4.RGB LED 电路
DIN 接到GPIO18上

## 5.MOS管驱动蜂鸣器电路
GPIO25 控制 N沟道MOS ，高电平导通，蜂鸣器鸣叫 ，低电平截止 ，蜂鸣器关闭

## 6.OLED屏幕驱动电路
OLED屏幕 连接到 I2C 总线上， OLED的SCL 接到 树莓派5的GPIO3_SCL上
OLED的SDA 接到 树莓派5的GPIO2_SDA上