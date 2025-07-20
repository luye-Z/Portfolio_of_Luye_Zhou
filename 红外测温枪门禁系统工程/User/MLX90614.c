#include "MLX90614.h"
#include "stm32f10x.h" // 标准库头文件
#include <stdio.h>
#include "./lcd/bsp_ili9341_lcd.h"

// 这里定义SA_W，注意是7位地址左移+写位(0)
#define SA 0x5A
#define SA_W 0xB4
#define SA_R 0xB5
#define GET_TEM_COMMAND 0x07
// 延时函数，72MHz CPU时钟，大致1us延时
  extern float temperature  ;
void I2C_Software_GPIO_Init(void)
{
    GPIO_InitTypeDef GPIO_InitStructure;

    // 1. 使能 GPIOB 时钟
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOB, ENABLE);

    // 2. 配置 PB6（SCL） 和 PB7（SDA）为开漏输出，高速50MHz
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_6 | GPIO_Pin_7;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_OD; // 开漏输出
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;

    GPIO_Init(GPIOB, &GPIO_InitStructure);

    // 3. 设置初始状态为高（释放总线）
    GPIO_SetBits(GPIOB, GPIO_Pin_6); // SCL 置高
    GPIO_SetBits(GPIOB, GPIO_Pin_7); // SDA 置高

    // first_iic_test();
}

void Delay_us(uint32_t us)
{
    volatile int i;
    while (us--)
    {
        for (i = 0; i < 72; i++)
        {
            __NOP();
        }
    }
}

#include "stm32f10x.h"

// 设置PB7 (SDA) 输出高电平
void Set_SDA_Output_High(void)
{
    GPIO_SetBits(GPIOB, GPIO_Pin_7);
}

// 设置PB7 (SDA) 输出低电平
void Set_SDA_Output_Low(void)
{
    GPIO_ResetBits(GPIOB, GPIO_Pin_7);
}

// 设置PB6 (SCL) 输出高电平
void Set_SCL_Output_High(void)
{
    GPIO_SetBits(GPIOB, GPIO_Pin_6);
}

// 设置PB6 (SCL) 输出低电平
void Set_SCL_Output_Low(void)
{
    GPIO_ResetBits(GPIOB, GPIO_Pin_6);
}

// 设置PB7为输入模式（释放SDA线）
void Set_SDA_Input_Mode(void)
{
    GPIO_InitTypeDef GPIO_InitStructure;

    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_7;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IN_FLOATING; // 悬空输入
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;

    GPIO_Init(GPIOB, &GPIO_InitStructure);
}

// 设置PB7为开漏输出模式（主动驱动SDA线）
void Set_SDA_Output_Mode(void)
{
    GPIO_InitTypeDef GPIO_InitStructure;

    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_7;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_OD; // 开漏输出
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;

    GPIO_Init(GPIOB, &GPIO_InitStructure);
}

// 设置PB7为开漏输出模式（用于模拟I2C时输出SDA）
void Set_SDA_Output_OpenDrain(void)
{
    GPIO_InitTypeDef GPIO_InitStructure;

    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_7;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_OD; // 开漏输出
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;

    GPIO_Init(GPIOB, &GPIO_InitStructure);
}

void ack_adjust(uint8_t ack)
{

    if (ack == 0)
    {
        ILI9341_DispStringLine_EN(LINE(2), "IIC_MLX90614_init_successful!");
    }
    else
    {
        ILI9341_DispStringLine_EN(LINE(2), "IIC_MLX90614_init_fail !");
    }
}

void MLX90614_STOP(void)
{
    Set_SDA_Output_OpenDrain();
    Set_SCL_Output_Low();
    Set_SDA_Output_Low();
    Delay_us(2);
    Set_SCL_Output_High();
    Delay_us(2);
    Set_SDA_Output_High();
    Delay_us(2);
}

// ************高级函数，主要调用的高级函数，封装了很多较为低级的API******************************/

void first_iic_test(void)
{

    // uint8_t dataL, dataH;
    // uint16_t temp_raw;
    // float temperature;

    MLX906_START();
    ack_adjust(MLX90614_Send_SA_W());
}

// 发送I2C起始信号
void MLX906_START(void)
{
    Set_SDA_Output_OpenDrain();
    Set_SCL_Output_High();
    Set_SDA_Output_High();
    Delay_us(2);
    Set_SDA_Output_Low();
    Delay_us(2);
    Set_SCL_Output_Low();
    Delay_us(1);
}

float MLX9_LCD_show_temperature(void) // 执行SMBUS协议流程 ， 并且通过计算，把温度显示在LCD屏幕上
{
    char temp_str[32];
    uint8_t dataL, dataH;
    uint16_t temp_raw;
  

    MLX906_START();
    MLX90614_Send_SA_W();
    MLX90614_Send_COMMAND();
    MLX906_START(); // Repeat start
    MLX90614_Send_SA_R();

    dataL = I2C_Read_Byte(1); // 读低字节，主机发ACK
    dataH = I2C_Read_Byte(1); // 读高字节，主机发ACK
    I2C_Read_Byte(0);         // 读PEC字节，主机发NACK

    MLX90614_STOP();

    temp_raw = ((uint16_t)dataH << 8) | dataL;
    temperature = temp_raw * 0.02 - 273.15; // 转换为摄氏度    char temp_str[32];

    // if (temperature > 1000 || temperature < -100)
    // {
    //     MLX90614_SoftReset(); // 强制释放总线，重新初始化
    // }

    sprintf(temp_str, "Temperature: %.2f C ", temperature);
    ILI9341_DispStringLine_EN(LINE(6), temp_str);
    //		 Delay_us(2);
    return temperature;
}

uint8_t I2C_Read_Byte(uint8_t ack)
{
    uint8_t i, byte = 0;
    Set_SDA_Input_Mode(); // 设置 SDA 为输入

    for (i = 0; i < 8; i++)
    {
        byte <<= 1;
        Set_SCL_Output_High();
        Delay_us(2);
        if (GPIO_ReadInputDataBit(GPIOB, GPIO_Pin_7))
            byte |= 0x01;
        Set_SCL_Output_Low();
        Delay_us(2);
    }

    // 发送ACK or NACK
    Set_SDA_Output_OpenDrain();
    if (ack)
        Set_SDA_Output_Low(); // ACK (拉低)
    else
        Set_SDA_Output_High(); // NACK (释放)

    Delay_us(2);
    Set_SCL_Output_High();
    Delay_us(2);
    Set_SCL_Output_Low();
    Delay_us(2);

    Set_SDA_Output_High(); // 释放 SDA
    return byte;
}

// 发送1字节数据，返回ACK(0)或NACK(1)
uint8_t I2C_Send_Byte(uint8_t byte)
{
    uint8_t i, ack;
    Set_SDA_Output_OpenDrain();

    for (i = 0; i < 8; i++)
    {
        if (byte & 0x80)
            Set_SDA_Output_High();
        else
            Set_SDA_Output_Low();

        Delay_us(2);
        Set_SCL_Output_High();
        Delay_us(2);
        Set_SCL_Output_Low();
        Delay_us(2);

        byte <<= 1;
    }

    // 释放SDA线，等待ACK
    Set_SDA_Output_High();
    Delay_us(2);

    Set_SDA_Input_Mode();

    Set_SCL_Output_High();
    Delay_us(2);

    ack = GPIO_ReadInputDataBit(GPIOB, GPIO_Pin_7); // 0表示ACK，1表示NACK

    Set_SCL_Output_Low();
    Set_SDA_Output_OpenDrain();

    return ack;
}

// 发送从机地址写命令，返回ACK状态
uint8_t MLX90614_Send_SA_W(void)
{
    // MLX906_START();
    return I2C_Send_Byte(SA_W);
}
// 发送从机地址读命令，返回ACK状态
uint8_t MLX90614_Send_SA_R(void)
{
    // MLX906_START();
    return I2C_Send_Byte(SA_R);
}

uint8_t MLX90614_Send_COMMAND(void)
{
    return I2C_Send_Byte(GET_TEM_COMMAND);
}

void MLX90614_SoftReset(void)
{
    uint8_t i;

    // Step 1: 检查 SDA 是否被拉低
    Set_SDA_Input_Mode();
    if (GPIO_ReadInputDataBit(GPIOB, GPIO_Pin_7) == 0) // SDA 被拉低
    {
        // Step 2: 模拟发送 9 个时钟释放 SDA
        Set_SDA_Output_OpenDrain(); // 拉高 SDA
        Set_SDA_Output_High();

        for (i = 0; i < 9; i++)
        {
            Set_SCL_Output_Low();
            Delay_us(5);
            Set_SCL_Output_High(); // 发送上升沿
            Delay_us(5);
        }

        // Step 3: 发送 STOP 信号（恢复总线）
        MLX90614_STOP();
    }

    // Step 4: 延时后重新初始化
    Delay_us(100);
    first_iic_test(); // 重新发送起始 & 地址，看能否恢复
}
