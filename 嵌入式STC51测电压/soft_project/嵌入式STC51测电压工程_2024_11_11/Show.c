      
#include "oled.h"

// OLED 显示转换结果
void  show(void)
	
	{
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