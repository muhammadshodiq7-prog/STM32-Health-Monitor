#ifndef __MODBUS_H
#define __MODBUS_H

#include "stm32f10x.h"

// Modbus功能码
#define MODBUS_FUNC_READ_HOLDING    0x03
#define MODBUS_FUNC_READ_INPUT      0x04
#define MODBUS_FUNC_WRITE_SINGLE    0x06
#define MODBUS_FUNC_WRITE_MULTIPLE  0x10

// Modbus响应
void Modbus_Process_Request(uint8_t *rx_buffer, uint16_t rx_length,
                          uint16_t *input_registers, uint16_t *holding_registers);

// CRC16计算
uint16_t Modbus_CRC16(uint8_t *data, uint16_t length);

// 发送响应
void Modbus_Send_Response(uint8_t *buffer, uint16_t length);

// 发送错误响应
void Modbus_Error_Response(uint8_t function_code, uint8_t exception_code);

#endif
