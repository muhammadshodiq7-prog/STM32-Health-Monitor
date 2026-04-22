#include "adc.h"
#include "delay.h"

void ADCx_Init(void)
{
    GPIO_InitTypeDef GPIO_InitStructure;
    ADC_InitTypeDef ADC_InitStructure;

    // 使能时钟
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_ADC1 | RCC_APB2Periph_GPIOA, ENABLE);

    // 配置ADC引脚
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_0 | GPIO_Pin_1;  // PA0(温度) PA1(心率)
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AIN;
    GPIO_Init(GPIOA, &GPIO_InitStructure);

    // ADC配置
    ADC_InitStructure.ADC_Mode = ADC_Mode_Independent;
    ADC_InitStructure.ADC_ScanConvMode = DISABLE;
    ADC_InitStructure.ADC_ContinuousConvMode = DISABLE;
    ADC_InitStructure.ADC_ExternalTrigConv = ADC_ExternalTrigConv_None;
    ADC_InitStructure.ADC_DataAlign = ADC_DataAlign_Right;
    ADC_InitStructure.ADC_NbrOfChannel = 1;
    ADC_Init(ADC1, &ADC_InitStructure);

    // 使能ADC
    ADC_Cmd(ADC1, ENABLE);

    // ADC校准
    ADC_ResetCalibration(ADC1);
    while(ADC_GetResetCalibrationStatus(ADC1));
    ADC_StartCalibration(ADC1);
    while(ADC_GetCalibrationStatus(ADC1));
}

uint16_t Get_Adc_Value(uint8_t channel)
{
    // 设置ADC通道
    ADC_RegularChannelConfig(ADC1, channel, 1, ADC_SampleTime_239Cycles5);

    // 启动转换
    ADC_SoftwareStartConvCmd(ADC1, ENABLE);

    // 等待转换完成
    while(!ADC_GetFlagStatus(ADC1, ADC_FLAG_EOC));

    // 读取结果
    return ADC_GetConversionValue(ADC1);
}