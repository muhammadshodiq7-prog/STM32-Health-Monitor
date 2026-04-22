#ifndef __IIC_H
#define __IIC_H

#include "stm32f10x.h"
#include "delay.h"

// -------------------------- 引脚配置（根据硬件修改） --------------------------
#define IIC_PORT        GPIOB
#define IIC_SCL_PIN     GPIO_Pin_6
#define IIC_SDA_PIN     GPIO_Pin_7
#define RCC_IIC_PORT    RCC_APB2Periph_GPIOB

// -------------------------- 函数式宏定义（匹配()调用） --------------------------
#define IIC_SDA_1()     GPIO_SetBits(IIC_PORT, IIC_SDA_PIN)    // 带括号！
#define IIC_SDA_0()     GPIO_ResetBits(IIC_PORT, IIC_SDA_PIN)  // 带括号！
#define IIC_SCL_1()     GPIO_SetBits(IIC_PORT, IIC_SCL_PIN)    // 带括号！
#define IIC_SCL_0()     GPIO_ResetBits(IIC_PORT, IIC_SCL_PIN)  // 带括号！

// -------------------------- 兼容原代码的IC_前缀 --------------------------
#define IC_SDA_1()      IIC_SDA_1()
#define IC_SDA_0()      IIC_SDA_0()
#define IC_SCL_1()      IIC_SCL_1()
#define IC_SCL_0()      IIC_SCL_0()

// -------------------------- 替换错误的DA_IN() --------------------------
#define DA_IN()         SDA_IN()  // 完全兼容原代码
#define SDA_IN()        do{ \
                            GPIO_InitTypeDef GPIO_InitStruct; \
                            GPIO_InitStruct.GPIO_Pin = IIC_SDA_PIN; \
                            GPIO_InitStruct.GPIO_Mode = GPIO_Mode_IN_FLOATING; \
                            GPIO_InitStruct.GPIO_Speed = GPIO_Speed_50MHz; \
                            GPIO_Init(IIC_PORT, &GPIO_InitStruct); \
                        }while(0)

#define SDA_OUT()       do{ \
                            GPIO_InitTypeDef GPIO_InitStruct; \
                            GPIO_InitStruct.GPIO_Pin = IIC_SDA_PIN; \
                            GPIO_InitStruct.GPIO_Mode = GPIO_Mode_Out_OD; \
                            GPIO_InitStruct.GPIO_Speed = GPIO_Speed_50MHz; \
                            GPIO_Init(IIC_PORT, &GPIO_InitStruct); \
                        }while(0)

#define READ_SDA        GPIO_ReadInputDataBit(IIC_PORT, IIC_SDA_PIN)

// -------------------------- 函数声明 --------------------------
void IIC_Init(void);
void IIC_Start(void);
void IIC_Stop(void);
uint8_t IIC_Wait_Ack(void);
void IIC_Ack(void);
void IIC_NAck(void);
void IIC_Send_Byte(uint8_t txd);
uint8_t IIC_Read_Byte(uint8_t ack);

#endif 
						