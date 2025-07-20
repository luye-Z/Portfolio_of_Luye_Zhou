#ifndef __BUZZER_H
#define __BUZZER_H

#include "stm32f10x.h"

void BUZZER_Init(void);
void BUZZER_Set(uint8_t state);
void BUZZER_Beep(uint8_t delay_time);
void BUZZER_On(void);
void BUZZER_Off(void);

#endif
