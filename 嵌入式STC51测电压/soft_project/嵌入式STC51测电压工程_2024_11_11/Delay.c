#include <intrins.h>


void Delay1500ms(void)	//@12.000MHz
{
	unsigned char data i, j, k;

	_nop_();
	i = 12;
	j = 103;
	k = 57;
	do
	{
		do
		{
			while (--k);
		} while (--j);
	} while (--i);
}


void Delay200ms(void)	//@12.000MHz
{
	unsigned char data i, j, k;

	_nop_();
	i = 2;
	j = 134;
	k = 20;
	do
	{
		do
		{
			while (--k);
		} while (--j);
	} while (--i);
}

