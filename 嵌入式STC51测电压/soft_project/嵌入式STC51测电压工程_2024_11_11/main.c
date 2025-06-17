// 部分代码借鉴于互联网
// 测控2202   周禄也   学号：202213630
// 单片机型号STC89C52RC

//////////////////////////////////////////////////////////////////////////////////////////////////

//              GND    电源地
//              VCC    接5V或3.3V电源
//              SCL    P2^0（SCL）
//              SDA    P2^1（SDA）


#include <reg52.h>
//#include "REG51.h"
#include "oled.h"
#include "bmp.h"
#include <intrins.h>
#include "Delay.h"
#include "baojing.h"


sbit OE = P3^0;            // ADC0809的OE端连接到51单片机P30
sbit EOC = P3^1;           // ADC0809的EOC端连接到51单片机P31  
                           // A/D转换结束信号，输出，当A/D转换结束时，此端输出一个高电平（转换期间一直为低电平）。
sbit CLOCK = P2^6;         // ADC0809的CLO连接到51单片机P26 
                           // CLK：时钟脉冲输入端。要求时钟频率不高于640KHZ。
sbit ST = P3^2;            // ADC0809的START和ALE

unsigned char dat[4] = {0, 0, 0, 0};  // 显示缓冲区
unsigned char adc;                  // 存放转换后的数据
unsigned int input;                 



void huanying(void)
{
    OLED_ShowCHinese(13, 0, 16);  // 欢迎你！
    OLED_ShowCHinese(29, 0, 17); 
    OLED_ShowCHinese(45, 0, 18); 
    OLED_ShowString(61, 0, "!", 16);   
    OLED_ShowString(10, 2, " Hope you have   a good day !", 16); 
    
    Delay1500ms();
}



void Delay(void)  // 延时大约83.33μs，防止OLED闪烁
{
    unsigned char i;
    for (i = 0; i < 250; i++);
}

// 定时计数器0的中断服务子程序
void timer0(void) interrupt 1 using 1  // 255微秒中断一次
{
    CLOCK = ~CLOCK;
}

// 主函数
int main(void)
{
    EA = 1; 
    ET0 = 1; 
    TMOD = 0x02;  // T0方式2计时  
                   // TH0 作为重装初值寄存器，
                   // TL0 作为计数寄存器。当 TL0 计数溢出后，会自动将 TH0 中的值重新装入 TL0 继续计数。
    TH0 = 0x01;    // 晶振：12MHz     
    TL0 = 0x01;    // 晶振：12MHz     
    TR0 = 1;       // 开中断,启动定时器

    OLED_Init();   // 初始化OLED  
    OLED_Clear();  
    huanying();
    OLED_Clear(); 
    P0 = 0xFF;
    
    while (1) 
    { 
        ST = 0;
        ST = 1;
        ST = 0;         // 启动转换
        while (!EOC);   // 等待转换结束
        
        OE = 1;         // 允许输出
        adc = P1;       // 取转换结果

        // 利用除法取余处理数据
        input = adc * 196.08;  // 转换成电压值
        dat[3] = input / 10000;    // 取电压数据最高位
        dat[2] = input / 1000 % 10;  // 取电压数据小数点后第一位
        dat[1] = input / 100 % 10;   // 取电压数据小数点后第二位
        dat[0] = input / 10 % 10;    // 取电压数据小数点后第三位
        
        if ((dat[3] >= 4) && (dat[2] >= 6) || (dat[3] == 5))
        {
			
			OLED_Clear(); 
			baojing();        // 调用报警函数  baojing.c  baojing.h
				
		 
        }

        // OLED 显示转换结果
        OLED_ShowCHinese(20, 0, 0);  // 显示 "电" 字（索引0）  
        OLED_ShowCHinese(36, 0, 1);  // 显示 "压" 字（索引1）  
        OLED_ShowCHinese(52, 0, 15); // 显示 "值" 字（索引15）  
        OLED_ShowString(68, 0, ":", 16);  // 显示小数点

        OLED_ShowNum(20, 2, dat[3], 1, 16);  // 显示最高位
        OLED_ShowString(30, 2, ".", 16);     // 显示小数点
        OLED_ShowNum(40, 2, dat[2], 1, 16);  // 小数点后第一位
        OLED_ShowNum(50, 2, dat[1], 1, 16);  // 小数点后第二位
        OLED_ShowNum(60, 2, dat[0], 1, 16);  // 小数点后第三位
        OLED_ShowString(70, 2, "V", 16);     // 显示单位“V”
        OLED_ShowString(58, 6, "by", 16);
        
        OLED_ShowCHinese(78, 6, 2);  
        OLED_ShowCHinese(94, 6, 3);  
        OLED_ShowCHinese(110, 6, 4);  

        Delay();  // 延时，避免闪烁
    }
}
