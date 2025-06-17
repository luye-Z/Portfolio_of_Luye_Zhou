// ���ִ������ڻ�����
// ���2202   ��»Ҳ   ѧ�ţ�202213630
// ��Ƭ���ͺ�STC89C52RC

//////////////////////////////////////////////////////////////////////////////////////////////////

//              GND    ��Դ��
//              VCC    ��5V��3.3V��Դ
//              SCL    P2^0��SCL��
//              SDA    P2^1��SDA��


#include <reg52.h>
//#include "REG51.h"
#include "oled.h"
#include "bmp.h"
#include <intrins.h>
#include "Delay.h"
#include "baojing.h"


sbit OE = P3^0;            // ADC0809��OE�����ӵ�51��Ƭ��P30
sbit EOC = P3^1;           // ADC0809��EOC�����ӵ�51��Ƭ��P31  
                           // A/Dת�������źţ��������A/Dת������ʱ���˶����һ���ߵ�ƽ��ת���ڼ�һֱΪ�͵�ƽ����
sbit CLOCK = P2^6;         // ADC0809��CLO���ӵ�51��Ƭ��P26 
                           // CLK��ʱ����������ˡ�Ҫ��ʱ��Ƶ�ʲ�����640KHZ��
sbit ST = P3^2;            // ADC0809��START��ALE

unsigned char dat[4] = {0, 0, 0, 0};  // ��ʾ������
unsigned char adc;                  // ���ת���������
unsigned int input;                 



void huanying(void)
{
    OLED_ShowCHinese(13, 0, 16);  // ��ӭ�㣡
    OLED_ShowCHinese(29, 0, 17); 
    OLED_ShowCHinese(45, 0, 18); 
    OLED_ShowString(61, 0, "!", 16);   
    OLED_ShowString(10, 2, " Hope you have   a good day !", 16); 
    
    Delay1500ms();
}



void Delay(void)  // ��ʱ��Լ83.33��s����ֹOLED��˸
{
    unsigned char i;
    for (i = 0; i < 250; i++);
}

// ��ʱ������0���жϷ����ӳ���
void timer0(void) interrupt 1 using 1  // 255΢���ж�һ��
{
    CLOCK = ~CLOCK;
}

// ������
int main(void)
{
    EA = 1; 
    ET0 = 1; 
    TMOD = 0x02;  // T0��ʽ2��ʱ  
                   // TH0 ��Ϊ��װ��ֵ�Ĵ�����
                   // TL0 ��Ϊ�����Ĵ������� TL0 ��������󣬻��Զ��� TH0 �е�ֵ����װ�� TL0 ����������
    TH0 = 0x01;    // ����12MHz     
    TL0 = 0x01;    // ����12MHz     
    TR0 = 1;       // ���ж�,������ʱ��

    OLED_Init();   // ��ʼ��OLED  
    OLED_Clear();  
    huanying();
    OLED_Clear(); 
    P0 = 0xFF;
    
    while (1) 
    { 
        ST = 0;
        ST = 1;
        ST = 0;         // ����ת��
        while (!EOC);   // �ȴ�ת������
        
        OE = 1;         // �������
        adc = P1;       // ȡת�����

        // ���ó���ȡ�ദ������
        input = adc * 196.08;  // ת���ɵ�ѹֵ
        dat[3] = input / 10000;    // ȡ��ѹ�������λ
        dat[2] = input / 1000 % 10;  // ȡ��ѹ����С������һλ
        dat[1] = input / 100 % 10;   // ȡ��ѹ����С�����ڶ�λ
        dat[0] = input / 10 % 10;    // ȡ��ѹ����С��������λ
        
        if ((dat[3] >= 4) && (dat[2] >= 6) || (dat[3] == 5))
        {
			
			OLED_Clear(); 
			baojing();        // ���ñ�������  baojing.c  baojing.h
				
		 
        }

        // OLED ��ʾת�����
        OLED_ShowCHinese(20, 0, 0);  // ��ʾ "��" �֣�����0��  
        OLED_ShowCHinese(36, 0, 1);  // ��ʾ "ѹ" �֣�����1��  
        OLED_ShowCHinese(52, 0, 15); // ��ʾ "ֵ" �֣�����15��  
        OLED_ShowString(68, 0, ":", 16);  // ��ʾС����

        OLED_ShowNum(20, 2, dat[3], 1, 16);  // ��ʾ���λ
        OLED_ShowString(30, 2, ".", 16);     // ��ʾС����
        OLED_ShowNum(40, 2, dat[2], 1, 16);  // С������һλ
        OLED_ShowNum(50, 2, dat[1], 1, 16);  // С�����ڶ�λ
        OLED_ShowNum(60, 2, dat[0], 1, 16);  // С��������λ
        OLED_ShowString(70, 2, "V", 16);     // ��ʾ��λ��V��
        OLED_ShowString(58, 6, "by", 16);
        
        OLED_ShowCHinese(78, 6, 2);  
        OLED_ShowCHinese(94, 6, 3);  
        OLED_ShowCHinese(110, 6, 4);  

        Delay();  // ��ʱ��������˸
    }
}
