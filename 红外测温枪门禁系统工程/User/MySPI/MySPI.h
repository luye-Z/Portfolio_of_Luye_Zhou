#ifndef _MYSPI_H_
#define _MYSPI_H_

#include "stm32f10x.h"
#include "MySPI.h"
#include <stdint.h>
/*
����ͼ��
��Դ3��3Vǧ��ע�⣡������������������������
��Դ 3.3Vǧ��ע�⣡������������������������
��Դ3��3Vǧ��ע�⣡������������������������
��Դ 3.3Vǧ��ע�⣡������������������������
��Դ3��3Vǧ��ע�⣡������������������������
��Դ 3.3Vǧ��ע�⣡������������������������
RST  A12   -> �������
MISO A3    -> ��������
MOSI A6  -> �������
SCK  A2    -> �������
CS   A4    -> �������
*/

// �궨�壺������˿�
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
