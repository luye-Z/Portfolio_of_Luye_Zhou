#ifndef _MLX90614_H_
#define _MLX90614_H_

#include "stm32f10x.h"   
//连线图
//
// 配置PB6 (SCL) 和 PB7 (SDA) 为开漏输出，速度50MHz
//

#define I2C_SCL_GPIO_Port GPIOB
#define I2C_SCL_Pin GPIO_PIN_6
#define I2C_SDA_GPIO_Port GPIOB
#define I2C_SDA_Pin GPIO_PIN_7
#define SA_W  0xB4 
void first_iic_test(void);
void MLX90614_Init(void);
void Delay_us(uint32_t us);
void Set_SDA_Output_OpenDrain(void);
void Set_SDA_Input_Mode(void);
void Set_SCL_Output_Low(void);
void Set_SCL_Output_High(void);
void Set_SDA_Output_Low(void);
void Set_SDA_Output_High(void);
void ack_adjust ( uint8_t ack );
void MLX90614_STOP(void);
float MLX9_LCD_show_temperature(void);
uint8_t I2C_Read_Byte(uint8_t ack);
uint8_t MLX90614_Send_SA_R(void);
uint8_t I2C_Wait_Ack(void);
uint8_t I2C_Send_Byte(uint8_t byte);
uint8_t MLX90614_Send_SA_W(void);
void MLX906_START(void);
uint8_t MLX90614_Send_COMMAND(void);
void I2C_Software_GPIO_Init(void);
void MLX90614_SoftReset(void);

#endif
