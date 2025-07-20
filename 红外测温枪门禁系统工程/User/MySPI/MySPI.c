#include "stm32f10x.h"
#include "MySPI.h"
#include <stdint.h>
/*
����ͼ��
RST  A12   -> �������
MISO A3    -> ��������
MOSI A6  -> �������
SCK  A2    -> �������
CS   A4    -> �������
*/




void RST_refresh (void)
{
	  GPIO_ResetBits(RST_PORT, RST_PIN);
		Delay_ms( 5);
	 GPIO_SetBits(RST_PORT, RST_PIN);
		Delay_ms( 5 );
}


// д CS ���ŵ�ƽ���߻�ͣ�
void MySPI_WriteCS(uint8_t state)
{
    if (state)
        GPIO_SetBits(CS_PORT, CS_PIN);
    else
        GPIO_ResetBits(CS_PORT, CS_PIN);
}

// д SCK
void MySPI_WriteSCK(uint8_t state)
{
    if (state)
        GPIO_SetBits(SCK_PORT, SCK_PIN);
    else
        GPIO_ResetBits(SCK_PORT, SCK_PIN);
}

// д MOSI
void MySPI_WriteMOSI(uint8_t state)
{
    if (state)
        GPIO_SetBits(MOSI_PORT, MOSI_PIN);
    else
        GPIO_ResetBits(MOSI_PORT, MOSI_PIN);
}

// д RST
void MySPI_WriteRST(uint8_t state)
{
    if (state)
        GPIO_SetBits(RST_PORT, RST_PIN);
    else
        GPIO_ResetBits(RST_PORT, RST_PIN);
}

// �� MISO
uint8_t MySPI_ReadMISO(void)
{
    return GPIO_ReadInputDataBit(MISO_PORT, MISO_PIN);
}

// SPI ��ʼ��
void MySPI_Init(void)
{
    GPIO_InitTypeDef GPIO_InitStructure;

    // ���� GPIOA ʱ��
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);

    // MOSI��SCK��RST��CS �������
    GPIO_InitStructure.GPIO_Pin = MOSI_PIN | SCK_PIN | RST_PIN | CS_PIN;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOA, &GPIO_InitStructure);

    // MISO ��������
    GPIO_InitStructure.GPIO_Pin = MISO_PIN;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IPU;
    GPIO_Init(GPIOA, &GPIO_InitStructure);

    //  ���Ÿߵ͵�ƽ��ʼ��
    MySPI_WriteCS(1);
    MySPI_WriteSCK(0);
}

void MySPI_Start(void) // ��ʼ�ź�

{
    MySPI_WriteCS(0); //  Ƭѡ�ź����ͣ���ʼSPIͨ��
    MySPI_WriteSCK(0); // ����״̬ҲҪ��ʱ���źŵ�ƽ����
}

void MySPI_Stop(void) //  ������ֹ�ź�

{
    MySPI_WriteSCK(0); // ����״̬ҲҪ��ʱ���źŵ�ƽ����
    MySPI_WriteCS(1);
}

uint8_t MySpi_Swapbyte(uint8_t Send_Message)
{
    uint8_t i, receive_message = 0x00;

    for (i = 0; i < 8; i++)
    {
        // ?? ǿ�Ʊ�� 0 �� 1��������ֱ�Ӵ�����λֵ
        MySPI_WriteMOSI((Send_Message & 0x80) ? 1 : 0);
        Send_Message <<= 1;

        MySPI_WriteSCK(1);
        __NOP(); __NOP(); __NOP(); // ���ֶ����ȶ�
        receive_message <<= 1;
        if (MySPI_ReadMISO())
            receive_message |= 0x01;

        MySPI_WriteSCK(0);
    }

    return receive_message;
}



void Delay_ms(uint32_t ms)
{
    uint32_t i, j;
    for (i = 0; i < ms; i++)
    {
        // һ����ѭ����Լ���� 1 ΢���ʱ�䣬��Ҫ����
        for (j = 0; j < 72 * 8000; j++)
        {
            __NOP(); // �ղ�������ֹ���Ż���
        }
    }
}
