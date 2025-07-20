#include "BUZZER.h"
#include "stm32f10x.h"
#include "Delay.h"
#include <stdio.h>

// 初始化蜂鸣器 IO：PA8 推挽输出
void BUZZER_Init(void)
{
    GPIO_InitTypeDef GPIO_InitStructure;

    // 开启 GPIOA 时钟
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);

    // 配置 PA8 为 推挽输出
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_8;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;
    GPIO_Init(GPIOA, &GPIO_InitStructure);

    // 默认关闭蜂鸣器（低电平）
    GPIO_ResetBits(GPIOA, GPIO_Pin_8);
}

// 设置蜂鸣器状态：1 = 响，0 = 静音
void BUZZER_Beep(uint8_t delay_time)  //  10  MS
{

    BUZZER_On();
    delay_10ms(delay_time);
    BUZZER_Off();
}
void BUZZER_On(void)
{
  GPIO_SetBits(GPIOA, GPIO_Pin_8);    // 高电平 → 响
}
void BUZZER_Off(void)
{
 GPIO_ResetBits(GPIOA, GPIO_Pin_8);  // 低电平 → 静音
}



