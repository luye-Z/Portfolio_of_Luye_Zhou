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

volatile uint16_t AvgPeriod0;  // ���0��ƽ������
volatile uint16_t AvgPeriod2;  // ���1��ƽ������

void PeriodMeasure0(uint16_t time) {
    static uint16_t First0 = 0;
    static uint32_t Sum0 = 0;
    static uint16_t Count0 = 0;

    uint16_t Period0 = (time - First0) & 0xFFFF;  // ��������
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

    uint16_t Period2 = (time - First2) & 0xFFFF;  // ��������
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
    Clock_Init48MHz();  // ��ʼ��ϵͳʱ��
    TimerA3Capture_Init(&PeriodMeasure0, &PeriodMeasure2);  // ��ʼ�� Timer A3 ����

    LaunchPad_Init();   // ��ʼ�� LaunchPad �ϵĿ��غ� LED
    Motor_Init();       // ��ʼ���������

    int left = 4000;    // ������ʼ�ٶ�
    int right = 4000;   // �ҵ����ʼ�ٶ�
    Motor_Forward(left, right); // ���Ƶ��ǰ��

    // LCD ��ʼ������ʾ����ٶ�
    JN_LCD_Init();
    while (1) {
        // �������ҵ����ת�٣�rpm��
        float pulses_per_rev = 7.0 * 4.0;  // ÿȦ�����������ı�Ƶ������
        float leftRPM = 60000000.0 / AvgPeriod0 / pulses_per_rev;    // 60000000 ��Ӧ�� 48 MHz
        float rightRPM = 60000000.0 / AvgPeriod2 / pulses_per_rev;

        // ��� LCD ��Ļ����ʾ���ת��
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

        Clock_Delay1ms(500);  // ������ʱʱ�䵽500���룬��0.5��
    }
}
