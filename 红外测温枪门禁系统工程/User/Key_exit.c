#include "Key_exit.h"
#include "stm32f10x.h"


// PA0 , KEY1
extern unsigned int USER_MODE;
void KEY_EXTI_Init(void)
{
    GPIO_InitTypeDef GPIO_InitStructure;
    EXTI_InitTypeDef EXTI_InitStructure;
    NVIC_InitTypeDef NVIC_InitStructure;
    /* ���� GPIOA �� AFIO ʱ�� */
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_AFIO, ENABLE);

    /* ���� PA0 Ϊ�������� */

    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IPU; // ��������
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_0;     // PA0
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOA, &GPIO_InitStructure); // !!! ����Ϊ GPIOA

    /* �� EXTI_Line0 ӳ�䵽 GPIOA0 */
    GPIO_EXTILineConfig(GPIO_PortSourceGPIOA, GPIO_PinSource0);

    /* ���� EXTI_Line0 */

    EXTI_InitStructure.EXTI_Line = EXTI_Line0; // 0����
    EXTI_InitStructure.EXTI_LineCmd = ENABLE;
    EXTI_InitStructure.EXTI_Mode = EXTI_Mode_Interrupt;
    EXTI_InitStructure.EXTI_Trigger = EXTI_Trigger_Falling; // �½��ش���
    // EXTI_InitStructure.EXTI_Trigger = EXTI_Trigger_Rising; //�����س�������
    EXTI_Init(&EXTI_InitStructure);

    /* �����жϷ��飨����ȫ�ֵ���һ�μ��ɣ� */
    NVIC_PriorityGroupConfig(NVIC_PriorityGroup_2); // ��ռ���ȼ�2λ����Ӧ���ȼ�2λ

    /* ���� NVIC��EXTI0 ��Ӧ���ж�ͨ���� EXTI0_IRQn */

    NVIC_InitStructure.NVIC_IRQChannel = EXTI0_IRQn; // !!! ����Ϊ EXTI0_IRQn
    NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 1;
    NVIC_InitStructure.NVIC_IRQChannelSubPriority = 1;
    NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;
    NVIC_Init(&NVIC_InitStructure);
}
// �жϷ����������� EXTI0 �ж�

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

