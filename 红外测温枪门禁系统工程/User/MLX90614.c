#include "MLX90614.h"
#include "stm32f10x.h" // ��׼��ͷ�ļ�
#include <stdio.h>
#include "./lcd/bsp_ili9341_lcd.h"

// ���ﶨ��SA_W��ע����7λ��ַ����+дλ(0)
#define SA 0x5A
#define SA_W 0xB4
#define SA_R 0xB5
#define GET_TEM_COMMAND 0x07
// ��ʱ������72MHz CPUʱ�ӣ�����1us��ʱ
  extern float temperature  ;
void I2C_Software_GPIO_Init(void)
{
    GPIO_InitTypeDef GPIO_InitStructure;

    // 1. ʹ�� GPIOB ʱ��
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOB, ENABLE);

    // 2. ���� PB6��SCL�� �� PB7��SDA��Ϊ��©���������50MHz
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_6 | GPIO_Pin_7;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_OD; // ��©���
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;

    GPIO_Init(GPIOB, &GPIO_InitStructure);

    // 3. ���ó�ʼ״̬Ϊ�ߣ��ͷ����ߣ�
    GPIO_SetBits(GPIOB, GPIO_Pin_6); // SCL �ø�
    GPIO_SetBits(GPIOB, GPIO_Pin_7); // SDA �ø�

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

// ����PB7 (SDA) ����ߵ�ƽ
void Set_SDA_Output_High(void)
{
    GPIO_SetBits(GPIOB, GPIO_Pin_7);
}

// ����PB7 (SDA) ����͵�ƽ
void Set_SDA_Output_Low(void)
{
    GPIO_ResetBits(GPIOB, GPIO_Pin_7);
}

// ����PB6 (SCL) ����ߵ�ƽ
void Set_SCL_Output_High(void)
{
    GPIO_SetBits(GPIOB, GPIO_Pin_6);
}

// ����PB6 (SCL) ����͵�ƽ
void Set_SCL_Output_Low(void)
{
    GPIO_ResetBits(GPIOB, GPIO_Pin_6);
}

// ����PB7Ϊ����ģʽ���ͷ�SDA�ߣ�
void Set_SDA_Input_Mode(void)
{
    GPIO_InitTypeDef GPIO_InitStructure;

    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_7;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IN_FLOATING; // ��������
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;

    GPIO_Init(GPIOB, &GPIO_InitStructure);
}

// ����PB7Ϊ��©���ģʽ����������SDA�ߣ�
void Set_SDA_Output_Mode(void)
{
    GPIO_InitTypeDef GPIO_InitStructure;

    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_7;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_OD; // ��©���
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;

    GPIO_Init(GPIOB, &GPIO_InitStructure);
}

// ����PB7Ϊ��©���ģʽ������ģ��I2Cʱ���SDA��
void Set_SDA_Output_OpenDrain(void)
{
    GPIO_InitTypeDef GPIO_InitStructure;

    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_7;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_OD; // ��©���
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

// ************�߼���������Ҫ���õĸ߼���������װ�˺ܶ��Ϊ�ͼ���API******************************/

void first_iic_test(void)
{

    // uint8_t dataL, dataH;
    // uint16_t temp_raw;
    // float temperature;

    MLX906_START();
    ack_adjust(MLX90614_Send_SA_W());
}

// ����I2C��ʼ�ź�
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

float MLX9_LCD_show_temperature(void) // ִ��SMBUSЭ������ �� ����ͨ�����㣬���¶���ʾ��LCD��Ļ��
{
    char temp_str[32];
    uint8_t dataL, dataH;
    uint16_t temp_raw;
  

    MLX906_START();
    MLX90614_Send_SA_W();
    MLX90614_Send_COMMAND();
    MLX906_START(); // Repeat start
    MLX90614_Send_SA_R();

    dataL = I2C_Read_Byte(1); // �����ֽڣ�������ACK
    dataH = I2C_Read_Byte(1); // �����ֽڣ�������ACK
    I2C_Read_Byte(0);         // ��PEC�ֽڣ�������NACK

    MLX90614_STOP();

    temp_raw = ((uint16_t)dataH << 8) | dataL;
    temperature = temp_raw * 0.02 - 273.15; // ת��Ϊ���϶�    char temp_str[32];

    // if (temperature > 1000 || temperature < -100)
    // {
    //     MLX90614_SoftReset(); // ǿ���ͷ����ߣ����³�ʼ��
    // }

    sprintf(temp_str, "Temperature: %.2f C ", temperature);
    ILI9341_DispStringLine_EN(LINE(6), temp_str);
    //		 Delay_us(2);
    return temperature;
}

uint8_t I2C_Read_Byte(uint8_t ack)
{
    uint8_t i, byte = 0;
    Set_SDA_Input_Mode(); // ���� SDA Ϊ����

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

    // ����ACK or NACK
    Set_SDA_Output_OpenDrain();
    if (ack)
        Set_SDA_Output_Low(); // ACK (����)
    else
        Set_SDA_Output_High(); // NACK (�ͷ�)

    Delay_us(2);
    Set_SCL_Output_High();
    Delay_us(2);
    Set_SCL_Output_Low();
    Delay_us(2);

    Set_SDA_Output_High(); // �ͷ� SDA
    return byte;
}

// ����1�ֽ����ݣ�����ACK(0)��NACK(1)
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

    // �ͷ�SDA�ߣ��ȴ�ACK
    Set_SDA_Output_High();
    Delay_us(2);

    Set_SDA_Input_Mode();

    Set_SCL_Output_High();
    Delay_us(2);

    ack = GPIO_ReadInputDataBit(GPIOB, GPIO_Pin_7); // 0��ʾACK��1��ʾNACK

    Set_SCL_Output_Low();
    Set_SDA_Output_OpenDrain();

    return ack;
}

// ���ʹӻ���ַд�������ACK״̬
uint8_t MLX90614_Send_SA_W(void)
{
    // MLX906_START();
    return I2C_Send_Byte(SA_W);
}
// ���ʹӻ���ַ���������ACK״̬
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

    // Step 1: ��� SDA �Ƿ�����
    Set_SDA_Input_Mode();
    if (GPIO_ReadInputDataBit(GPIOB, GPIO_Pin_7) == 0) // SDA ������
    {
        // Step 2: ģ�ⷢ�� 9 ��ʱ���ͷ� SDA
        Set_SDA_Output_OpenDrain(); // ���� SDA
        Set_SDA_Output_High();

        for (i = 0; i < 9; i++)
        {
            Set_SCL_Output_Low();
            Delay_us(5);
            Set_SCL_Output_High(); // ����������
            Delay_us(5);
        }

        // Step 3: ���� STOP �źţ��ָ����ߣ�
        MLX90614_STOP();
    }

    // Step 4: ��ʱ�����³�ʼ��
    Delay_us(100);
    first_iic_test(); // ���·�����ʼ & ��ַ�����ܷ�ָ�
}
