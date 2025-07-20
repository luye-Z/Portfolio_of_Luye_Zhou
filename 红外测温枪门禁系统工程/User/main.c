
#include "stm32f10x.h"
#include "bsp_ili9341_lcd.h"
#include "bsp_usart.h"
#include <stdio.h>
#include "RC522.h"
#include "MySPI.h"
#include "MLX90614.h"
#include "Delay.h"
#include "LED.h"
#include "BUZZER.h"
#include "Key_exit.h"
#include "Relay.h"

/// @brief ///////
/// @param nCount
///
///
void Delay(__IO uint32_t nCount);

/////////////
void After_Found_Card(void);
void Running_Light(unsigned int time_counts); //  参数说明，流水灯循环的次数
void Show_User_Mode(void);
void Temperature_Check(float temp);
/////////////////////********全局变量*****************////////////////////////
unsigned char id_find_card = 0; //   0 没有找到卡
uint8_t Now_Card_UID[UID_LENGTH] = {0};
float temperature = 0;
float now_temp = 0;
float measure_body_temperature = 0;
unsigned int USER_MODE = 0;
unsigned int Is_relay_on = 0 ; 
/////////////////////////////////////////////////////////////////

int main(void)
{
  ///////////////// 初始化函数 /////////////////

  ILI9341_Init(); // LCD 初始化
  // USART_Config();
  // // ILI9341_GramScan(6);
  // LCD_screen_fonts_init();

  MySPI_Init();
  I2C_Software_GPIO_Init();
  RST_refresh();
  RFID_Init();
  LED_Init();
  BUZZER_Init();
  KEY_EXTI_Init();
	Relay_GPIO_Config();

  /////////////////****************************************** */

  //////////////初始化测试函数//////////////////////
  // ILI9341_DispStringLine_EN(LINE(1), "HELLO_WORLD!");
  // RCC52_first_test();
  // Test_ReadRawRC();
  // test_WriteRawRC();

  ////////////////////////////////////////
  // Running_Light(3);
		LED_Cyan_On();
//    Relay_Off();  //  初始化关闭 继电器
  // BUZZER_Beep(5);  ///////初始化成功，提示音乐
  ////////////////////////////////////////
  while (1)
  {
			if(USER_MODE==0 )  //  仅仅温度显示功能
	{
		  Show_User_Mode();
		  now_temp = MLX9_LCD_show_temperature();
	}
	else if (USER_MODE ==1 )
	{
		  Show_User_Mode();
		Rc522Test();
		 if (id_find_card == 1) // 如果找到卡了，进入一个处理函数 ， AFTER_FIND_CARD
    {
     delay_10ms(150);
    }
	}
	else  if (USER_MODE == 2  )
	{
    Show_User_Mode();
    now_temp = MLX9_LCD_show_temperature();
    measure_body_temperature = now_temp;
    // Temperature_Check(now_temp);
    Rc522Test();
    if (id_find_card == 1) // 如果找到卡了，进入一个处理函数 ， AFTER_FIND_CARD
    {
      After_Found_Card();
    }

    Delay(1);
	}
	else if (USER_MODE == 3 )
	{
    Show_User_Mode();
    now_temp = MLX9_LCD_show_temperature();
    measure_body_temperature = now_temp;
    // Temperature_Check(now_temp);
    Rc522Test();
    if (id_find_card == 1) // 如果找到卡了，进入一个处理函数 ， AFTER_FIND_CARD
    {
      After_Found_Card();
    }

    Delay(1);
	}
  }
}

/**
 * @brief  简单延时函数
 * @param  nCount ：延时计数值
 * @retval 无
 */
static void Delay(__IO uint32_t nCount)
{
  for (; nCount != 0; nCount--)
    ;
}

void After_Found_Card(void)

{

  // char display_str[50];
  // sprintf(display_str, "UID: %02X %02X %02X %02X",
  //         Now_Card_UID[0], Now_Card_UID[1], Now_Card_UID[2], Now_Card_UID[3]);
  // ILI9341_DispStringLine_EN(LINE(3), display_str);

  if (Adjust_if_card_knowm() == 1) // 这张卡在系统中录入过
  {

    ILI9341_DispStringLine_EN(LINE(3), "Welcomeback !");

    if ((measure_body_temperature > 30) && (measure_body_temperature < 37.4))
    {
      ILI9341_DispStringLine_EN(LINE(4), "Temperature healthy !");
      LED_Green_On();
      BUZZER_On();
    }

	
    else
    {
      ILI9341_DispStringLine_EN(LINE(4), "Please Re-measure your body temperature!");

      BUZZER_On();
      LED_Flash(RED_LED, 7); // 红灯闪烁三次
    }
  }
  else
  {

    ILI9341_DispStringLine_EN(LINE(3), "illegal access!");
    BUZZER_On();
    LED_Flash(RED_LED, 7); // 红灯闪烁三次
  }
  delay_10ms(100);
  /////////////一切工作都做完之后，执行下面这些。
  ILI9341_DispStringLine_EN(LINE(3), "                                     "); // 清空这两行屏幕
  ILI9341_DispStringLine_EN(LINE(4), "                                     ");
  ILI9341_DispStringLine_EN(LINE(5), "                                     ");
  id_find_card = 0; //  0 代表着没找到卡,更新全局标志变量。
  LED_Cyan_On();
  BUZZER_Off();
}

void Running_Light(unsigned int time_counts) //  参数说明，流水灯循环的次数
{
  unsigned int count = 0;
  for (count = 0; count < time_counts; count++)
  {
    LED_Flash(RED_LED, 1);    // 红灯闪烁三次
    LED_Flash(GREEN_LED, 1);  // 红灯闪烁三次
    LED_Flash(BLUE_LED, 1);   // 红灯闪烁三次
    LED_Flash(PURPLE_LED, 1); // 红灯闪烁三
    LED_Flash(YELLOW_LED, 1); // 红灯闪烁三
    LED_Flash(CYAN_LED, 1);   // 红灯闪烁三
  }
}

void Temperature_Check(float temp)
{
  if (temp > 1000 || temp < -100)
  {
    MLX90614_SoftReset(); // 强制释放总线，重新初始化
  }
}

void Show_User_Mode(void)
{
  if (USER_MODE == 0)
  {
			ILI9341_DispStringLine_EN(LINE(1), " MODE 0 Temperature detect ");
		 ILI9341_DispStringLine_EN(LINE(15), "                                            ");
		 ILI9341_DispStringLine_EN(LINE(16), "                                            ");
		 ILI9341_DispStringLine_EN(LINE(17), "                                            ");
  }
  else if (USER_MODE == 1)
  {
    ILI9341_DispStringLine_EN(LINE(1), " MODE 1 CARD DETECTED                          ");
		 ILI9341_DispStringLine_EN(LINE(6), "                                            ");
  }
  else if (USER_MODE == 2)
  {
    ILI9341_DispStringLine_EN(LINE(1), " MODE 2 WORK_MODE                        ");
  }
  else if (USER_MODE == 3)
  {
    ILI9341_DispStringLine_EN(LINE(1), " MODE 3 DEVELOP_TEST                       ");
  }
}
