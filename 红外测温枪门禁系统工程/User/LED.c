#include "LED.h"
#include "stm32f10x.h"
#include "Delay.h"

// ��ʼ�� LED ��Ӧ�� GPIO��PB0, PB1, PB5��

void LED_Init(void)
{
    GPIO_InitTypeDef GPIO_InitStructure;

    // ���� GPIOB ʱ��
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOB, ENABLE);

    // ���� PB0, PB1, PB5 Ϊ �������
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_0 | GPIO_Pin_1 | GPIO_Pin_5;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;

    GPIO_Init(GPIOB, &GPIO_InitStructure);

    // ��ʼ״̬��ȫ����Ϊ������LED��IO�ڸߵ�ƽ����ƣ�
    GPIO_SetBits(GPIOB, GPIO_Pin_0 | GPIO_Pin_1 | GPIO_Pin_5);
}

// ����ĳ�� LED��0 ��ʾ����1 ��ʾ��
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
        return; // ������Χ
    }

    if (state == 0)
        GPIO_ResetBits(GPIOB, pin); // ����͵�ƽ �� LED ��
    else
        GPIO_SetBits(GPIOB, pin); // ����ߵ�ƽ �� LED ��
}

// ����LED��
void LED_AllOn(void)
{
    GPIO_ResetBits(GPIOB, GPIO_Pin_0 | GPIO_Pin_1 | GPIO_Pin_5);
}

// ����LED��
void LED_AllOff(void)
{
    GPIO_SetBits(GPIOB, GPIO_Pin_0 | GPIO_Pin_1 | GPIO_Pin_5);
}
// ��Ϩ�����еƣ�Ȼ��������
void LED_Red_On(void)
{
    GPIO_SetBits(GPIOB, GPIO_Pin_0 | GPIO_Pin_1 | GPIO_Pin_5);
    GPIO_ResetBits(GPIOB, GPIO_Pin_5);
}

// ��Ϩ�����еƣ�Ȼ������̵�
void LED_Green_On(void)
{
    GPIO_SetBits(GPIOB, GPIO_Pin_0 | GPIO_Pin_1 | GPIO_Pin_5);
    GPIO_ResetBits(GPIOB, GPIO_Pin_0);
}
// ��Ϩ�����еƣ�Ȼ���������
void LED_Blue_On(void)
{
    GPIO_SetBits(GPIOB, GPIO_Pin_0 | GPIO_Pin_1 | GPIO_Pin_5);
    GPIO_ResetBits(GPIOB, GPIO_Pin_1);
}
void LED_Yellow_On(void) // �� + ��
{
    GPIO_SetBits(GPIOB, GPIO_Pin_0 | GPIO_Pin_1 | GPIO_Pin_5);
    GPIO_ResetBits(GPIOB, GPIO_Pin_0 | GPIO_Pin_5); // ������������
}

void LED_Cyan_On(void) // �� + ��
{
    GPIO_SetBits(GPIOB, GPIO_Pin_0 | GPIO_Pin_1 | GPIO_Pin_5);
    GPIO_ResetBits(GPIOB, GPIO_Pin_1 | GPIO_Pin_0); // �غ죬������
}

void LED_White_On(void) // �� + �� + ��
{
    GPIO_ResetBits(GPIOB, GPIO_Pin_0 | GPIO_Pin_1 | GPIO_Pin_5); // ȫ��
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
            delay_10ms(35); // Լ350ms
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
