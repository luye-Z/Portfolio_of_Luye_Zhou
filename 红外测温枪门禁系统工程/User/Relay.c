#include "stm32f10x.h"
#include "Relay.h"


//��������  �ź�����  PC8
//VCC  3.3    GND 

void Relay_GPIO_Config(void)
{
	 GPIO_InitTypeDef GPIO_InitStructure;
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOC, ENABLE);  // ����GPIOCʱ��


    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_8;             // PC8
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;      // �������
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;     // ����ٶ�
    GPIO_Init(GPIOC, &GPIO_InitStructure);

    GPIO_SetBits(GPIOC, GPIO_Pin_8); // Ĭ�Ϲرռ̵���������ߵ�ƽ��
}

void Relay_On(void)
{
    GPIO_ResetBits(GPIOC, GPIO_Pin_8);  // ����͵�ƽ���̵�������
	Is_relay_on = 1; 
}

void Relay_Off(void)
{
    GPIO_SetBits(GPIOC, GPIO_Pin_8);   // ����ߵ�ƽ���̵����ͷ�
		Is_relay_on = 0;
}

void Change_relay_status(void)
{
	
if(Is_relay_on ==  0 )
{
Relay_On();
}
else 
{
	Relay_Off();
}

}
