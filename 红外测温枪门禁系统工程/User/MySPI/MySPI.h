#ifndef _MYSPI_H_
#define _MYSPI_H_

#include "stm32f10x.h"
#include "MySPI.h"
#include <stdint.h>
/*
接线图：
电源3。3V千万注意！！！！！！！！！！！！！
电源 3.3V千万注意！！！！！！！！！！！！！
电源3。3V千万注意！！！！！！！！！！！！！
电源 3.3V千万注意！！！！！！！！！！！！！
电源3。3V千万注意！！！！！！！！！！！！！
电源 3.3V千万注意！！！！！！！！！！！！！
RST  A12   -> 推挽输出
MISO A3    -> 上拉输入
MOSI A6  -> 推挽输出
SCK  A2    -> 推挽输出
CS   A4    -> 推挽输出
*/

// 宏定义：引脚与端口
#define RST_PIN GPIO_Pin_12
#define RST_PORT GPIOA

#define MISO_PIN GPIO_Pin_3
#define MISO_PORT GPIOA

#define MOSI_PIN GPIO_Pin_6
#define MOSI_PORT GPIOA

#define SCK_PIN GPIO_Pin_2
#define SCK_PORT GPIOA

#define CS_PIN GPIO_Pin_4
#define CS_PORT GPIOA

void MySPI_WriteCS(uint8_t state);

void MySPI_WriteSCK(uint8_t state);

void MySPI_WriteMOSI(uint8_t state);

void MySPI_WriteRST(uint8_t state);

uint8_t MySPI_ReadMISO(void);

void MySPI_Init(void);

void MySPI_Start(void);

void MySPI_Stop(void);
uint8_t  MySpi_Swapbyte(uint8_t Send_Message);
void Delay_ms(uint32_t ms);
void RST_refresh (void) ;

#endif
