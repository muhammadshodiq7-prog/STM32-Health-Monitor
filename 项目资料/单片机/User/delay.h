#ifndef __DELAY_H
#define __DELAY_H

#include "stm32f10x.h"

void delay_init(void);
void delay_ms(uint16_t ms);
void delay_us(uint32_t us);

// 新增函数声明
void SysTick_Init(void);
uint32_t Get_Tick(void);

#endif
