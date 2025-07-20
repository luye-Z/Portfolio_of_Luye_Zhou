#ifndef  _RELAY_H_
#define  _RELAY_H_


extern unsigned int Is_relay_on ; 
void Relay_GPIO_Config(void);
void Relay_On(void);
void Relay_Off(void);
	void Change_relay_status(void);
#endif
