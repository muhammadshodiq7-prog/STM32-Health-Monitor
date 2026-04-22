// usart.c
#include "usart.h"
#include "delay.h"

// 接收缓冲区（非static，供中断处理函数访问）
uint8_t USART1_RxBuffer[USART1_RECV_BUFFER_SIZE];
uint16_t USART1_RxWriteIndex = 0;
uint16_t USART1_RxReadIndex = 0;
volatile uint16_t USART1_RxCount = 0;
volatile uint8_t pc_connected = 0;
uint8_t rx_buffer[64];
uint8_t rx_len = 0;

// 发送缓冲区（可选，用于DMA或中断发送）
static uint8_t USART1_TxBuffer[USART1_SEND_BUFFER_SIZE];

/**
  * @brief  USART1初始化函数
  * @param  baudrate: 波特率，如9600, 115200等
  * @retval 无
  */
void USART1_Init(uint32_t baudrate)
{
    GPIO_InitTypeDef GPIO_InitStructure;
    USART_InitTypeDef USART_InitStructure;
    NVIC_InitTypeDef NVIC_InitStructure;
    
    // 1. 使能时钟
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_USART1 | RCC_APB2Periph_GPIOA | RCC_APB2Periph_AFIO, ENABLE);
    
    // 2. 配置USART1 Tx (PA9) 作为推挽复用输出
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_9;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_PP;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOA, &GPIO_InitStructure);
    
    // 3. 配置USART1 Rx (PA10) 作为浮空输入
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_10;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IN_FLOATING;
    GPIO_Init(GPIOA, &GPIO_InitStructure);
    
    // 4. 配置USART参数
    USART_InitStructure.USART_BaudRate = baudrate;
    USART_InitStructure.USART_WordLength = USART_WordLength_8b;
    USART_InitStructure.USART_StopBits = USART_StopBits_1;
    USART_InitStructure.USART_Parity = USART_Parity_No;
    USART_InitStructure.USART_HardwareFlowControl = USART_HardwareFlowControl_None;
    USART_InitStructure.USART_Mode = USART_Mode_Rx | USART_Mode_Tx;
    
    // 5. 初始化USART
    USART_Init(USART1, &USART_InitStructure);
    
    // 6. 配置USART1中断优先级（只使能接收中断）
    NVIC_InitStructure.NVIC_IRQChannel = USART1_IRQn;
    NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 1;
    NVIC_InitStructure.NVIC_IRQChannelSubPriority = 1;
    NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;
    NVIC_Init(&NVIC_InitStructure);
    
    // 7. 使能USART接收中断
    USART_ITConfig(USART1, USART_IT_RXNE, ENABLE);
    
    // 8. 使能USART
    USART_Cmd(USART1, ENABLE);
    
    // 9. 清除缓冲区
    USART1_ClearRxBuffer();
    
    // 10. 发送初始化成功信息
    USART1_SendString("\r\nUSART1 Initialized Successfully!\r\n");
    USART1_SendString("Baudrate: ");
    USART1_SendBytes((uint8_t *)&baudrate, sizeof(baudrate));
    USART1_SendString("\r\n");
}

/**
  * @brief  发送一个字节（阻塞方式）
  * @param  data: 要发送的字节
  * @retval 无
  */
void USART1_SendByte(uint8_t data)
{
    // 等待发送数据寄存器为空
    while(USART_GetFlagStatus(USART1, USART_FLAG_TXE) == RESET);
    
    // 发送数据
    USART_SendData(USART1, data);
    
    // 等待发送完成
    while(USART_GetFlagStatus(USART1, USART_FLAG_TC) == RESET);
}

/**
  * @brief  发送多个字节（阻塞方式）
  * @param  data: 数据指针
  * @param  length: 数据长度
  * @retval 无
  */
void USART1_SendBytes(uint8_t *data, uint16_t length)
{
    for(uint16_t i = 0; i < length; i++)
    {
        USART1_SendByte(data[i]);
    }
}

/**
  * @brief  发送字符串
  * @param  str: 字符串指针
  * @retval 无
  */
void USART1_SendString(char *str)
{
    while(*str != '\0')
    {
        USART1_SendByte((uint8_t)(*str));
        str++;
    }
}

/**
  * @brief  接收一个字节（非阻塞，从缓冲区读取）
  * @param  无
  * @retval 接收到的字节，如果缓冲区为空则返回0
  */
uint8_t USART1_ReceiveByte(void)
{
    uint8_t data = 0;
    
    // 如果缓冲区中有数据
    if(USART1_RxCount > 0)
    {
        // 读取数据
        data = USART1_RxBuffer[USART1_RxReadIndex];
        
        // 更新读索引
        USART1_RxReadIndex = (USART1_RxReadIndex + 1) % USART1_RECV_BUFFER_SIZE;
        
        // 减少计数
        USART1_RxCount--;
    }
    
    return data;
}

/**
  * @brief  接收多个字节
  * @param  buffer: 接收缓冲区
  * @param  max_length: 最大接收长度
  * @retval 实际接收到的字节数
  */
uint16_t USART1_ReceiveBytes(uint8_t *buffer, uint16_t max_length)
{
    uint16_t received = 0;
    
    while(USART1_RxCount > 0 && received < max_length)
    {
        buffer[received] = USART1_ReceiveByte();
        received++;
    }
    
    return received;
}

/**
  * @brief  获取接收缓冲区中的数据长度
  * @param  无
  * @retval 缓冲区中的数据字节数
  */
uint16_t USART1_GetRxLength(void)
{
    return USART1_RxCount;
}

/**
  * @brief  清空接收缓冲区
  * @param  无
  * @retval 无
  */
void USART1_ClearRxBuffer(void)
{
    USART1_RxWriteIndex = 0;
    USART1_RxReadIndex = 0;
    USART1_RxCount = 0;
}

/**
  * @brief  使能USART1中断
  * @param  无
  * @retval 无
  */
void USART1_EnableIRQ(void)
{
    USART_ITConfig(USART1, USART_IT_RXNE, ENABLE);
}

/**
  * @brief  禁用USART1中断
  * @param  无
  * @retval 无
  */
void USART1_DisableIRQ(void)
{
    USART_ITConfig(USART1, USART_IT_RXNE, DISABLE);
}

/**
  * @brief  发送Modbus帧（添加CRC校验）
  * @param  frame: Modbus帧数据（不包含CRC）
  * @param  length: 帧长度（不包含CRC）
  * @retval 发送状态
  */
USART_Status USART1_SendModbusFrame(uint8_t *frame, uint8_t length)
{
    uint16_t crc = 0xFFFF;
    uint8_t i, j;
    
    // 计算CRC16（Modbus RTU CRC）
    for(i = 0; i < length; i++)
    {
        crc ^= frame[i];
        for(j = 0; j < 8; j++)
        {
            if(crc & 0x0001)
            {
                crc = (crc >> 1) ^ 0xA001;
            }
            else
            {
                crc = crc >> 1;
            }
        }
    }
    
    // 发送原始数据
    USART1_SendBytes(frame, length);
    
    // 发送CRC（低字节在前，高字节在后）
    USART1_SendByte(crc & 0xFF);        // CRC低字节
    USART1_SendByte((crc >> 8) & 0xFF); // CRC高字节
    
    return USART_OK;
}

/**
  * @brief  USART1中断服务函数声明（在stm32f10x_it.c中实现）
  */

/**
  * @brief  重定向printf到串口1（可选）
  * @param  ch: 字符
  * @param  f: 文件指针
  * @retval 字符
  */
#if defined(__CC_ARM) || defined(__ICCARM__) || defined(__GNUC__)
PUTCHAR_PROTOTYPE
{
    // 发送字符
    while(USART_GetFlagStatus(USART1, USART_FLAG_TXE) == RESET);
    USART_SendData(USART1, (uint8_t)ch);
    
    // 等待发送完成
    while(USART_GetFlagStatus(USART1, USART_FLAG_TC) == RESET);
    
    return ch;
}
#endif
