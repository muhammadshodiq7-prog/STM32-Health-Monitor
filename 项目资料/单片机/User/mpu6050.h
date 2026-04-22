#ifndef __MPU6050_H
#define __MPU6050_H

#include "stm32f10x.h"

// MPU6050 I2C地址
#define MPU6050_ADDR    0xD0

// MPU6050寄存器地址
#define MPU6050_SELF_TEST_X    0x0D
#define MPU6050_SELF_TEST_Y    0x0E
#define MPU6050_SELF_TEST_Z    0x0F
#define MPU6050_SELF_TEST_A    0x10
#define MPU6050_SMPLRT_DIV     0x19
#define MPU6050_CONFIG         0x1A
#define MPU6050_GYRO_CONFIG    0x1B
#define MPU6050_ACCEL_CONFIG   0x1C
#define MPU6050_FIFO_EN        0x23
#define MPU6050_I2C_MST_CTRL   0x24
#define MPU6050_INT_PIN_CFG    0x37
#define MPU6050_INT_ENABLE     0x38
#define MPU6050_INT_STATUS     0x3A
#define MPU6050_ACCEL_XOUT_H   0x3B
#define MPU6050_ACCEL_XOUT_L   0x3C
#define MPU6050_ACCEL_YOUT_H   0x3D
#define MPU6050_ACCEL_YOUT_L   0x3E
#define MPU6050_ACCEL_ZOUT_H   0x3F
#define MPU6050_ACCEL_ZOUT_L   0x40
#define MPU6050_TEMP_OUT_H     0x41
#define MPU6050_TEMP_OUT_L     0x42
#define MPU6050_GYRO_XOUT_H    0x43
#define MPU6050_GYRO_XOUT_L    0x44
#define MPU6050_GYRO_YOUT_H    0x45
#define MPU6050_GYRO_YOUT_L    0x46
#define MPU6050_GYRO_ZOUT_H    0x47
#define MPU6050_GYRO_ZOUT_L    0x48
#define MPU6050_USER_CTRL      0x6A
#define MPU6050_PWR_MGMT_1     0x6B
#define MPU6050_PWR_MGMT_2     0x6C
#define MPU6050_FIFO_COUNTH    0x72
#define MPU6050_FIFO_COUNTL    0x73
#define MPU6050_FIFO_R_W       0x74
#define MPU6050_WHO_AM_I       0x75

// 加速度量程
typedef enum {
    MPU6050_ACCEL_RANGE_2G  = 0x00,
    MPU6050_ACCEL_RANGE_4G  = 0x08,
    MPU6050_ACCEL_RANGE_8G  = 0x10,
    MPU6050_ACCEL_RANGE_16G = 0x18
} MPU6050_AccelRange;

// 函数声明
uint8_t MPU6050_Init(void);
void MPU6050_WriteReg(uint8_t reg, uint8_t data);
uint8_t MPU6050_ReadReg(uint8_t reg);
void MPU6050_ReadAccel(float *x, float *y);
void MPU6050_ReadAccelAll(float *x, float *y, float *z);
void MPU6050_SetAccelRange(MPU6050_AccelRange range);
#endif
