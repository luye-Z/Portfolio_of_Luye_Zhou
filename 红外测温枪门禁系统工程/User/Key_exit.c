#include "Key_exit.h"
#include "stm32f10x.h"


// PA0 , KEY1
extern unsigned int USER_MODE;
void KEY_EXTI_Init(void)
{
    GPIO_InitTypeDef GPIO_InitStructure;
    EXTI_InitTypeDef EXTI_InitStructure;
    NVIC_InitTypeDef NVIC_InitStructure;
    /* 开启 GPIOA 和 AFIO 时钟 */
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_AFIO, ENABLE);

    /* 配置 PA0 为上拉输入 */

    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IPU; // 上拉输入
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_0;     // PA0
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOA, &GPIO_InitStructure); // !!! 修正为 GPIOA

    /* 将 EXTI_Line0 映射到 GPIOA0 */
    GPIO_EXTILineConfig(GPIO_PortSourceGPIOA, GPIO_PinSource0);

    /* 配置 EXTI_Line0 */

    EXTI_InitStructure.EXTI_Line = EXTI_Line0; // 0号线
    EXTI_InitStructure.EXTI_LineCmd = ENABLE;
    EXTI_InitStructure.EXTI_Mode = EXTI_Mode_Interrupt;
    EXTI_InitStructure.EXTI_Trigger = EXTI_Trigger_Falling; // 下降沿触发
    // EXTI_InitStructure.EXTI_Trigger = EXTI_Trigger_Rising; //上升沿除法触发
    EXTI_Init(&EXTI_InitStructure);

    /* 配置中断分组（此项全局调用一次即可） */
    NVIC_PriorityGroupConfig(NVIC_PriorityGroup_2); // 抢占优先级2位，响应优先级2位

    /* 配置 NVIC，EXTI0 对应的中断通道是 EXTI0_IRQn */

    NVIC_InitStructure.NVIC_IRQChannel = EXTI0_IRQn; // !!! 修正为 EXTI0_IRQn
    NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 1;
    NVIC_InitStructure.NVIC_IRQChannelSubPriority = 1;
    NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;
    NVIC_Init(&NVIC_InitStructure);
}
// 中断服务函数，处理 EXTI0 中断

void Change_Use_Mode(void)
{

    if (USER_MODE <= 2)
    {
        ++USER_MODE;
    }
    else if (USER_MODE == 3)
    {
        USER_MODE = 0;
    }
}

