#include "BUZZER.h"
#include "stm32f10x.h"
#include "Delay.h"
#include <stdio.h>

// ��ʼ�������� IO��PA8 �������
void BUZZER_Init(void)
{
    GPIO_InitTypeDef GPIO_InitStructure;

    // ���� GPIOA ʱ��
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);

    // ���� PA8 Ϊ �������
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_8;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;
    GPIO_Init(GPIOA, &GPIO_InitStructure);

    // Ĭ�Ϲرշ��������͵�ƽ��
    GPIO_ResetBits(GPIOA, GPIO_Pin_8);
}

// ���÷�����״̬��1 = �죬0 = ����
void BUZZER_Beep(uint8_t delay_time)  //  10  MS
{

    BUZZER_On();
    delay_10ms(delay_time);
    BUZZER_Off();
}
void BUZZER_On(void)
{
  GPIO_SetBits(GPIOA, GPIO_Pin_8);    // �ߵ�ƽ �� ��
}
void BUZZER_Off(void)
{
 GPIO_ResetBits(GPIOA, GPIO_Pin_8);  // �͵�ƽ �� ����
}



