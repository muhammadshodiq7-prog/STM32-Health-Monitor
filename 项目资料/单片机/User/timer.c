#include "timer.h"

/**
 * @brief  TIM2配置
 * @retval 无
 * @note   配置TIM2为100ms定时的基础定时器
 */
void TIM2_Configuration(void)
{
    // 定义定时器时基初始化结构体变量，用于存放定时器配置参数
    TIM_TimeBaseInitTypeDef TIM_TimeBaseStructure;

    /* 定时器基础配置 - 72MHz / 7200 = 10kHz, 100ms定时 */
    // TIM_Period：自动重装载值，计数到该值后溢出（1000个计数周期，对应100ms）
    TIM_TimeBaseStructure.TIM_Period = 1000 - 1;
    // TIM_Prescaler：预分频系数，72MHz系统时钟分频后得到10kHz计数时钟
    TIM_TimeBaseStructure.TIM_Prescaler = 7200 - 1;
    // TIM_ClockDivision：时钟分割比，设置为不分频（TIM_CKD_DIV1），不影响计数时钟
    TIM_TimeBaseStructure.TIM_ClockDivision = TIM_CKD_DIV1;
    // TIM_CounterMode：计数器模式，设置为向上计数模式（从0计数到自动重装载值）
    TIM_TimeBaseStructure.TIM_CounterMode = TIM_CounterMode_Up;

    // 根据配置的结构体参数，初始化TIM2定时器时基配置
    TIM_TimeBaseInit(TIM2, &TIM_TimeBaseStructure);
    // 将TIM2计数器值清零，确保定时器从0开始计数
    TIM_SetCounter(TIM2, 0);
}
