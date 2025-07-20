#include "LED.h"
#include "stm32f10x.h"
#include "Delay.h"

// 初始化 LED 对应的 GPIO（PB0, PB1, PB5）

void LED_Init(void)
{
    GPIO_InitTypeDef GPIO_InitStructure;

    // 开启 GPIOB 时钟
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOB, ENABLE);

    // 配置 PB0, PB1, PB5 为 推挽输出
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_0 | GPIO_Pin_1 | GPIO_Pin_5;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;

    GPIO_Init(GPIOB, &GPIO_InitStructure);

    // 初始状态：全灭（因为负极接LED，IO口高电平即灭灯）
    GPIO_SetBits(GPIOB, GPIO_Pin_0 | GPIO_Pin_1 | GPIO_Pin_5);
}

// 控制某个 LED：0 表示亮，1 表示灭
void LED_Set(uint8_t led_num, uint8_t state)
{
    uint16_t pin;

    switch (led_num)
    {
    case 0:
        pin = GPIO_Pin_0;
        break;
    case 1:
        pin = GPIO_Pin_1;
        break;
    case 2:
        pin = GPIO_Pin_5;
        break;
    default:
        return; // 超出范围
    }

    if (state == 0)
        GPIO_ResetBits(GPIOB, pin); // 输出低电平 → LED 亮
    else
        GPIO_SetBits(GPIOB, pin); // 输出高电平 → LED 灭
}

// 所有LED亮
void LED_AllOn(void)
{
    GPIO_ResetBits(GPIOB, GPIO_Pin_0 | GPIO_Pin_1 | GPIO_Pin_5);
}

// 所有LED灭
void LED_AllOff(void)
{
    GPIO_SetBits(GPIOB, GPIO_Pin_0 | GPIO_Pin_1 | GPIO_Pin_5);
}
// 先熄灭所有灯，然后点亮红灯
void LED_Red_On(void)
{
    GPIO_SetBits(GPIOB, GPIO_Pin_0 | GPIO_Pin_1 | GPIO_Pin_5);
    GPIO_ResetBits(GPIOB, GPIO_Pin_5);
}

// 先熄灭所有灯，然后点亮绿灯
void LED_Green_On(void)
{
    GPIO_SetBits(GPIOB, GPIO_Pin_0 | GPIO_Pin_1 | GPIO_Pin_5);
    GPIO_ResetBits(GPIOB, GPIO_Pin_0);
}
// 先熄灭所有灯，然后点亮蓝灯
void LED_Blue_On(void)
{
    GPIO_SetBits(GPIOB, GPIO_Pin_0 | GPIO_Pin_1 | GPIO_Pin_5);
    GPIO_ResetBits(GPIOB, GPIO_Pin_1);
}
void LED_Yellow_On(void) // 红 + 绿
{
    GPIO_SetBits(GPIOB, GPIO_Pin_0 | GPIO_Pin_1 | GPIO_Pin_5);
    GPIO_ResetBits(GPIOB, GPIO_Pin_0 | GPIO_Pin_5); // 关蓝，亮红绿
}

void LED_Cyan_On(void) // 绿 + 蓝
{
    GPIO_SetBits(GPIOB, GPIO_Pin_0 | GPIO_Pin_1 | GPIO_Pin_5);
    GPIO_ResetBits(GPIOB, GPIO_Pin_1 | GPIO_Pin_0); // 关红，亮绿蓝
}

void LED_White_On(void) // 红 + 绿 + 蓝
{
    GPIO_ResetBits(GPIOB, GPIO_Pin_0 | GPIO_Pin_1 | GPIO_Pin_5); // 全亮
}
void LED_Purple_On(void)
{
    GPIO_SetBits(GPIOB, GPIO_Pin_0 | GPIO_Pin_1 | GPIO_Pin_5);
    GPIO_ResetBits(GPIOB, GPIO_Pin_1 | GPIO_Pin_5);
}
void LED_Flash(unsigned int Color_type, unsigned flash_nums)
{
    unsigned int i = 0;
    if (Color_type == RED_LED)
    {
        for (i = 0; i < flash_nums; i++)
        {
            LED_AllOff();
            LED_Red_On();
            delay_10ms(35); // 约350ms
            LED_AllOff();
            delay_10ms(35);
        }
    }
    else if (Color_type == GREEN_LED)
    {
        for (i = 0; i < flash_nums; i++)
        {
            LED_AllOff();
            LED_Green_On();
            delay_10ms(35);
            LED_AllOff();
            delay_10ms(35);
        }
    }
    else if (Color_type == BLUE_LED)
    {
        for (i = 0; i < flash_nums; i++)
        {
            LED_AllOff();
            LED_Blue_On();
            delay_10ms(35);
            LED_AllOff();
            delay_10ms(35);
        }
    }
    else if (Color_type == PURPLE_LED)
    {
        for (i = 0; i < flash_nums; i++)
        {
            LED_AllOff();
            LED_Purple_On();
            delay_10ms(35);
            LED_AllOff();
            delay_10ms(35);
        }
    }
    else if (Color_type == CYAN_LED)
    {
        for (i = 0; i < flash_nums; i++)
        {
            LED_AllOff();
            LED_Cyan_On();
            delay_10ms(35);
            LED_AllOff();
            delay_10ms(35);
        }
    }
    else if (Color_type == YELLOW_LED)
    {
        for (i = 0; i < flash_nums; i++)
        {
            LED_AllOff();
            LED_Yellow_On();
            delay_10ms(35);
            LED_AllOff();
            delay_10ms(35);
        }
    }
    else if (Color_type == WHITE_LED)
    {
        for (i = 0; i < flash_nums; i++)
        {
            LED_AllOff();
            LED_White_On();
            delay_10ms(35);
            LED_AllOff();
            delay_10ms(35);
        }
    }
}
