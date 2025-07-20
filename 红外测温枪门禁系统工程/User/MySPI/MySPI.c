#include "stm32f10x.h"
#include "MySPI.h"
#include <stdint.h>
/*
接线图：
RST  A12   -> 推挽输出
MISO A3    -> 上拉输入
MOSI A6  -> 推挽输出
SCK  A2    -> 推挽输出
CS   A4    -> 推挽输出
*/




void RST_refresh (void)
{
	  GPIO_ResetBits(RST_PORT, RST_PIN);
		Delay_ms( 5);
	 GPIO_SetBits(RST_PORT, RST_PIN);
		Delay_ms( 5 );
}


// 写 CS 引脚电平（高或低）
void MySPI_WriteCS(uint8_t state)
{
    if (state)
        GPIO_SetBits(CS_PORT, CS_PIN);
    else
        GPIO_ResetBits(CS_PORT, CS_PIN);
}

// 写 SCK
void MySPI_WriteSCK(uint8_t state)
{
    if (state)
        GPIO_SetBits(SCK_PORT, SCK_PIN);
    else
        GPIO_ResetBits(SCK_PORT, SCK_PIN);
}

// 写 MOSI
void MySPI_WriteMOSI(uint8_t state)
{
    if (state)
        GPIO_SetBits(MOSI_PORT, MOSI_PIN);
    else
        GPIO_ResetBits(MOSI_PORT, MOSI_PIN);
}

// 写 RST
void MySPI_WriteRST(uint8_t state)
{
    if (state)
        GPIO_SetBits(RST_PORT, RST_PIN);
    else
        GPIO_ResetBits(RST_PORT, RST_PIN);
}

// 读 MISO
uint8_t MySPI_ReadMISO(void)
{
    return GPIO_ReadInputDataBit(MISO_PORT, MISO_PIN);
}

// SPI 初始化
void MySPI_Init(void)
{
    GPIO_InitTypeDef GPIO_InitStructure;

    // 开启 GPIOA 时钟
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);

    // MOSI、SCK、RST、CS 推挽输出
    GPIO_InitStructure.GPIO_Pin = MOSI_PIN | SCK_PIN | RST_PIN | CS_PIN;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOA, &GPIO_InitStructure);

    // MISO 上拉输入
    GPIO_InitStructure.GPIO_Pin = MISO_PIN;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IPU;
    GPIO_Init(GPIOA, &GPIO_InitStructure);

    //  引脚高低电平初始化
    MySPI_WriteCS(1);
    MySPI_WriteSCK(0);
}

void MySPI_Start(void) // 起始信号

{
    MySPI_WriteCS(0); //  片选信号拉低，开始SPI通信
    MySPI_WriteSCK(0); // 空闲状态也要把时钟信号电平拉低
}

void MySPI_Stop(void) //  传输终止信号

{
    MySPI_WriteSCK(0); // 空闲状态也要把时钟信号电平拉低
    MySPI_WriteCS(1);
}

uint8_t MySpi_Swapbyte(uint8_t Send_Message)
{
    uint8_t i, receive_message = 0x00;

    for (i = 0; i < 8; i++)
    {
        // ?? 强制变成 0 或 1，而不是直接传引脚位值
        MySPI_WriteMOSI((Send_Message & 0x80) ? 1 : 0);
        Send_Message <<= 1;

        MySPI_WriteSCK(1);
        __NOP(); __NOP(); __NOP(); // 保持短暂稳定
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
        // 一个空循环大约消耗 1 微秒的时间，需要调整
        for (j = 0; j < 72 * 8000; j++)
        {
            __NOP(); // 空操作，防止被优化掉
        }
    }
}
