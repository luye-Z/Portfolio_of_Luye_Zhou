      
#include "oled.h"

// OLED ��ʾת�����
void  show(void)
	
	{
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