#include "Delay.h"
#include "stm32f10x.h"


void delay_10ms(unsigned int _10ms)
{
    unsigned int i, j;

    for (i = 0; i < _10ms; i++)
    {
        for (j = 0; j < 60000; j++)
            ;
    }
}
