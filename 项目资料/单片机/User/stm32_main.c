/*
 * 生理数据监测系统 - STM32 主程序
 * 功能：
 * 1. 采集体温（热敏电阻，ADC）
 * 2. 采集心率（红外传感器，ADC + 阈值法）
 * 3. 采集加速度（MPU6050，I2C）
 * 4. OLED 实时显示
 * 5. 串口输出调试信息
 */

#include "stm32f10x.h"
#include "delay.h"
#include "usart.h"
#include "adc.h"
#include "iic.h"
#include "oled.h"
#include "mpu6050.h"
#include <math.h>
#include <string.h>

/* ================= 函数声明 ================= */
void RCC_Configuration(void);
void GPIO_Configuration(void);
uint8_t Read_Temperature_Sensor(float *temp);
uint8_t Read_HeartRate_Sensor(void);
void MPU6050_Read_Accel(int16_t *ax, int16_t *ay, int16_t *az);

volatile uint8_t monitor_running = 0; // 0: waiting, 1: running

/* ================= 主函数 ================= */
int main(void)
{
    float temperature = 0.0f;
    uint8_t heart_rate = 0;
    int16_t ax, ay, az;

    RCC_Configuration();
    GPIO_Configuration();
    delay_init();

    USART1_Init(9600);
    ADCx_Init();
    IIC_Init();

    OLED_Init();
    MPU6050_Init();
	

	if (strcmp((char *)rx_buffer, "START") == 0)
	{
		monitor_running = 1;
		OLED_ShowStatus(1);  // running...
	}

    while (1)
    {
        /* 读取温度 */
        Read_Temperature_Sensor(&temperature);

        /* 读取心率 */
        heart_rate = Read_HeartRate_Sensor();

        /* 读取加速度 */
		MPU6050_Read_Accel(&ax, &ay, &az);

        /* 串口调试输出 */
        printf("T: %.1f C, H: %d bpm, X:%d Y:%d Z:%d\r\n",
               temperature, heart_rate, ax, ay, az);
	OLED_Clear();
	OLED_ShowString(0, 2, (uint8_t *)"waiting.", 12);
	delay_ms(300);
	OLED_ShowString(0, 2, (uint8_t *)"waiting..", 12);
	delay_ms(300);
	OLED_ShowString(0, 2, (uint8_t *)"waiting...", 12);

    // ★ 检测是否与上位机建立连接
    static uint8_t last_state = 0;
    if (pc_connected && last_state == 0)
    {
        OLED_Clear();
        OLED_ShowString(0, 2, (uint8_t *)"running...", 12);
        last_state = 1;
    }
        delay_ms(500);
    }
}

/* ================= 外设初始化 ================= */
/**
 * @brief RCC 时钟配置
 */
void RCC_Configuration(void)
{
    RCC_APB2PeriphClockCmd(
        RCC_APB2Periph_GPIOA |
        RCC_APB2Periph_GPIOB |
        RCC_APB2Periph_GPIOC |
        RCC_APB2Periph_AFIO  |
        RCC_APB2Periph_USART1 |
        RCC_APB2Periph_ADC1,
        ENABLE
    );

    RCC_APB1PeriphClockCmd(RCC_APB1Periph_I2C1, ENABLE);

    RCC_ADCCLKConfig(RCC_PCLK2_Div6); // ADC 时钟 12MHz
}

/**
 * @brief GPIO 配置（与硬件接线一一对应）
 */
void GPIO_Configuration(void)
{
    GPIO_InitTypeDef GPIO_InitStructure;

    /* USART1 TX PA9 */
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_9;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_PP;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOA, &GPIO_InitStructure);

    /* USART1 RX PA10 */
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_10;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IN_FLOATING;
    GPIO_Init(GPIOA, &GPIO_InitStructure);

    /* I2C1 SCL PB6 */
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_6;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_OD;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOB, &GPIO_InitStructure);

    /* I2C1 SDA PB7 */
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_7;
    GPIO_Init(GPIOB, &GPIO_InitStructure);

    /* 按键 PC13（上拉输入，按下为 0） */
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_13;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IPU;
    GPIO_Init(GPIOC, &GPIO_InitStructure);
}

/* ================= 传感器读取函数 ================= */
/**
 * @brief 读取温度（热敏电阻）
 * @param temp 温度值指针
 * @retval 成功返回 1
 */
uint8_t Read_Temperature_Sensor(float *temp)
{
    uint16_t adc = Get_Adc_Value(ADC_Channel_0); // PA0

    /* ADC → 电压 */
    float voltage = adc * 3.3f / 4096.0f;
    float resistance = (3.3f - voltage) * 10000 / voltage;

    /* Steinhart-Hart 方程 */
    *temp = 1.0f /
            (0.001129148f +
             0.000234125f * log(resistance) +
             0.0000000876741f * pow(log(resistance), 3))
            - 273.15f;

    /* 一阶低通滤波 */
    static float temp_filter = 36.5f;
    temp_filter = temp_filter * 0.9f + (*temp) * 0.1f;
    *temp = temp_filter;

    return 1;
}

/**
 * @brief 读取心率（红外传感器）
 * @retval 心率值 bpm
 */
uint8_t Read_HeartRate_Sensor(void)
{
    static uint32_t last_peak_time = 0;
    static uint8_t bpm = 72;

    uint16_t adc = Get_Adc_Value(ADC_Channel_1); // PA1

    /* 阈值法检测脉搏峰值 */
    if (adc > 2000) {
        uint32_t now = TIM_GetCounter(TIM2);

        if (last_peak_time != 0) {
            uint32_t interval = now - last_peak_time;
            if (interval > 300 && interval < 2000) {
                bpm = 60000 / interval;
            }
        }

        last_peak_time = now;
        delay_ms(200); // 防抖
    }

    return bpm;
}

/**
 * @brief  读取 MPU6050 三轴加速度
 * @param  ax, ay, az：加速度原始数据（16位有符号）
 */
void MPU6050_Read_Accel(int16_t *ax, int16_t *ay, int16_t *az)
{
    uint8_t buffer[6]; // 存储6字节加速度原始数据（每轴2字节）

    // 第一步：发送写指令，指定加速度数据起始寄存器
    IIC_Start();                  // IIC起始信号
    IIC_Send_Byte(MPU6050_ADDR);  // 发送MPU6050设备写地址
    IIC_Wait_Ack();               // 等待设备应答
    IIC_Send_Byte(MPU6050_ACCEL_XOUT_H); // 发送加速度X轴高位寄存器地址
    IIC_Wait_Ack();               // 等待设备应答

    // 第二步：发送读指令，准备接收数据
    IIC_Start();                  // IIC重复起始信号
    IIC_Send_Byte(MPU6050_ADDR | 0x01); // 发送MPU6050设备读地址
    IIC_Wait_Ack();               // 等待设备应答

    // 第三步：读取6字节加速度数据（X/Y/Z轴各2字节）
    for (int i = 0; i < 6; i++)
    {
        if (i == 5)
            buffer[i] = IIC_Read_Byte(0); // 最后1字节读取后发送NACK（结束接收）
        else
            buffer[i] = IIC_Read_Byte(1); // 前5字节读取后发送ACK（继续接收）
    }
    IIC_Stop(); // IIC停止信号，结束通信

    // 第四步：拼接高低字节，转换为16位有符号加速度值
    *ax = (int16_t)((buffer[0] << 8) | buffer[1]); // X轴加速度值
    *ay = (int16_t)((buffer[2] << 8) | buffer[3]); // Y轴加速度值
    *az = (int16_t)((buffer[4] << 8) | buffer[5]); // Z轴加速度值
}
