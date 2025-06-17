#include <stdint.h>
#include "msp.h"
#include "../inc/Clock.h"
#include "../inc/LaunchPad.h"
#include "../inc/Motor.h"
#include "../inc/JN_LCD.h"
#include "../inc/TA3InputCapture.h"
#include "string.h"
#include "../inc/SysTick.h"
#include "../inc/Bump.h"
#include "../inc/PWM.h"
#include "..\inc\MotorSimple.h"

volatile uint16_t AvgPeriod0;  // 电机0的平均周期
volatile uint16_t AvgPeriod2;  // 电机1的平均周期

void PeriodMeasure0(uint16_t time) {
    static uint16_t First0 = 0;
    static uint32_t Sum0 = 0;
    static uint16_t Count0 = 0;

    uint16_t Period0 = (time - First0) & 0xFFFF;  // 计算周期
    First0 = time;

    if (Count0 == 0) {
        AvgPeriod0 = Period0;
    } else {
        Sum0 += Period0;
        AvgPeriod0 = Sum0 / Count0;
    }

    Count0++;
}

void PeriodMeasure2(uint16_t time) {
    static uint16_t First2 = 0;
    static uint32_t Sum2 = 0;
    static uint16_t Count2 = 0;

    uint16_t Period2 = (time - First2) & 0xFFFF;  // 计算周期
    First2 = time;

    if (Count2 == 0) {
        AvgPeriod2 = Period2;
    } else {
        Sum2 += Period2;
        AvgPeriod2 = Sum2 / Count2;
    }

    Count2++;
}

int main(void) {
    Clock_Init48MHz();  // 初始化系统时钟
    TimerA3Capture_Init(&PeriodMeasure0, &PeriodMeasure2);  // 初始化 Timer A3 捕获

    LaunchPad_Init();   // 初始化 LaunchPad 上的开关和 LED
    Motor_Init();       // 初始化电机控制

    int left = 4000;    // 左电机初始速度
    int right = 4000;   // 右电机初始速度
    Motor_Forward(left, right); // 控制电机前进

    // LCD 初始化和显示电机速度
    JN_LCD_Init();
    while (1) {
        // 计算左右电机的转速（rpm）
        float pulses_per_rev = 7.0 * 4.0;  // 每圈脉冲数乘以四倍频编码器
        float leftRPM = 60000000.0 / AvgPeriod0 / pulses_per_rev;    // 60000000 对应于 48 MHz
        float rightRPM = 60000000.0 / AvgPeriod2 / pulses_per_rev;

        // 清空 LCD 屏幕并显示电机转速
        JN_LCD_Clear_0();
        JN_LCD_Set_Pos(0, 0);
        JN_LCD_OutString("The motor speed:");
        JN_LCD_Set_Pos(10, 2);
        JN_LCD_OutString("L:");
        JN_LCD_OutUDec((uint32_t)leftRPM);
        JN_LCD_OutString(" r/min");
        JN_LCD_Set_Pos(10, 4);
        JN_LCD_OutString("R:");
        JN_LCD_OutUDec((uint32_t)rightRPM);
        JN_LCD_OutString(" r/min");
        JN_LCD_Set_Pos(85, 7);
        JN_LCD_OutString("by zly");

        Clock_Delay1ms(500);  // 减少延时时间到500毫秒，即0.5秒
    }
}
