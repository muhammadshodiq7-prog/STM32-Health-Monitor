#include "delay.h"

static uint8_t fac_us = 0;
static uint16_t fac_ms = 0;
static volatile uint32_t system_ticks = 0;  // 系统时钟计数器

void delay_init(void)
{
    // 配置SysTick时钟源
    SysTick_CLKSourceConfig(SysTick_CLKSource_HCLK_Div8);
    fac_us = SystemCoreClock / 8000000;
    fac_ms = (uint16_t)fac_us * 1000;
}

void delay_us(uint32_t us)
{
    // 使用简单的循环延时，不干扰SysTick
    uint32_t count = us * (SystemCoreClock / 8000000) / 5;
    while(count--);
}

void delay_ms(uint16_t ms)
{
    // 使用Get_Tick函数实现毫秒延时，不干扰SysTick
    uint32_t start = Get_Tick();
    while((Get_Tick() - start) < ms);
}

// 初始化SysTick定时器（1ms中断）
void SysTick_Init(void)
{
    // 配置SysTick为1ms中断
    if(SysTick_Config(SystemCoreClock / 1000))
    {
        while(1);  // 配置失败
    }
}

// 获取系统时钟计数（毫秒）
uint32_t Get_Tick(void)
{
    return system_ticks;
}

// SysTick中断服务函数
void SysTick_Handler(void)
{
    system_ticks++;
}