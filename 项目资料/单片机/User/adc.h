#ifndef __ADC_H
#define __ADC_H

#include "stm32f10x.h"

void ADCx_Init(void);
uint16_t Get_Adc_Value(uint8_t channel);

#endif