#ifndef __LED_H
#define __LED_H

#include "stm32f10x.h"
#define RED_LED 1 
#define GREEN_LED 2
#define BLUE_LED 3
#define WHITE_LED 4 
#define YELLOW_LED 5 
#define  PURPLE_LED 6
#define  CYAN_LED 7
void LED_Init(void);
void LED_Set(uint8_t led_num, uint8_t state);
void LED_AllOn(void);
void LED_AllOff(void);
void LED_Red_On(void);
void LED_Green_On(void);
void LED_Blue_On(void);
void LED_Flash(unsigned int Color_type , unsigned flash_nums );
void LED_White_On(void) ;// ╨Л + бл + ю╤
void LED_Cyan_On(void) ;// бл + ю╤
void LED_Yellow_On(void); // ╨Л + бл
void LED_Magenta_On(void);
#endif
