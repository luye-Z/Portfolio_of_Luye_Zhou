#include "stm32f10x.h"
#include "Relay.h"


//引脚连接  信号引脚  PC8
//VCC  3.3    GND 

void Relay_GPIO_Config(void)
{
	 GPIO_InitTypeDef GPIO_InitStructure;
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOC, ENABLE);  // 开启GPIOC时钟


    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_8;             // PC8
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;      // 推挽输出
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;     // 输出速度
    GPIO_Init(GPIOC, &GPIO_InitStructure);

    GPIO_SetBits(GPIOC, GPIO_Pin_8); // 默认关闭继电器（输出高电平）
}

void Relay_On(void)
{
    GPIO_ResetBits(GPIOC, GPIO_Pin_8);  // 输出低电平，继电器吸合
	Is_relay_on = 1; 
}

void Relay_Off(void)
{
    GPIO_SetBits(GPIOC, GPIO_Pin_8);   // 输出高电平，继电器释放
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
