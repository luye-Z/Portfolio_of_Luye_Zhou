#include "oled.h"
#include <reg52.h>
#include "Delay.h"

void baojing(void)
{
	int count = 0;
    OLED_ShowCHinese(5, 2, 5);              // 超出电压报警！！！，请按
    OLED_ShowCHinese(21, 2, 6);  
    OLED_ShowCHinese(37, 2, 0);    
    OLED_ShowCHinese(53, 2, 1);  	
    OLED_ShowCHinese(69, 2, 7);      
    OLED_ShowCHinese(85, 2, 8);  
    OLED_ShowString(103, 2, "!!!", 16);  
    OLED_ShowCHinese(5, 4, 9);  
    OLED_ShowCHinese(21, 4, 10);      
    OLED_ShowCHinese(37, 4, 11);  
    OLED_ShowCHinese(53, 4, 12);      
    OLED_ShowCHinese(69, 4, 13);  
    OLED_ShowCHinese(85, 4, 14);  
	
	
	 while (1)
            {
                P0 = P0 ^ 0x01;  // 对 P0.0 引脚的状态进行取反
                Delay200ms(); 
				count++;
				
				if(count>=14)
				{
					
				OLED_Clear(); 
				baojing();   
				count =0 ;
					
				}
                
            }
}