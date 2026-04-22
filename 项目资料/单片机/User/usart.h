// usart.h
#ifndef __USART_H
#define __USART_H

#include "stm32f10x.h"
#include <stdio.h>

// 串口定义
#define USART1_RECV_BUFFER_SIZE 256
#define USART1_SEND_BUFFER_SIZE 256

// 串口状态枚举
typedef enum {
    USART_OK = 0,
    USART_ERROR,
    USART_BUSY,
    USART_TIMEOUT
} USART_Status;

// 串口配置结构体
typedef struct {
    uint32_t baudrate;
    uint16_t word_length;
    uint16_t stop_bits;
    uint16_t parity;
    uint16_t mode;
    uint16_t hardware_flow_control;
} USART_InitType;

// 函数声明
void USART1_Init(uint32_t baudrate);
void USART1_SendByte(uint8_t data);
void USART1_SendBytes(uint8_t *data, uint16_t length);
void USART1_SendString(char *str);
uint8_t USART1_ReceiveByte(void);
uint16_t USART1_ReceiveBytes(uint8_t *buffer, uint16_t max_length);
uint16_t USART1_GetRxLength(void);
void USART1_ClearRxBuffer(void);
void USART1_EnableIRQ(void);
void USART1_DisableIRQ(void);
USART_Status USART1_SendModbusFrame(uint8_t *frame, uint8_t length);

// 外部变量声明（用于中断处理）
extern uint8_t USART1_RxBuffer[];
extern uint16_t USART1_RxWriteIndex;
extern uint16_t USART1_RxReadIndex;
extern volatile uint16_t USART1_RxCount;
#define USART1_RECV_BUFFER_SIZE 256
// 重定向printf到串口1
#ifdef __GNUC__
    #define PUTCHAR_PROTOTYPE int __io_putchar(int ch)
#else
    #define PUTCHAR_PROTOTYPE int fputc(int ch, FILE *f)
#endif
#endif
	