#include "mpu6050.h"
#include "iic.h"
#include "delay.h"
#include "math.h"

// 加速度比例因子
static float accel_scale = 16384.0f;  // ±2g量程时的比例因子

// 写寄存器
void MPU6050_WriteReg(uint8_t reg, uint8_t data)
{
    IIC_Start();
    IIC_Send_Byte(MPU6050_ADDR);
    IIC_Wait_Ack();
    IIC_Send_Byte(reg);
    IIC_Wait_Ack();
    IIC_Send_Byte(data);
    IIC_Wait_Ack();
    IIC_Stop();
}

// 读寄存器
uint8_t MPU6050_ReadReg(uint8_t reg)
{
    uint8_t data;
    IIC_Start();
    IIC_Send_Byte(MPU6050_ADDR);
    IIC_Wait_Ack();
    IIC_Send_Byte(reg);
    IIC_Wait_Ack();
    IIC_Start();
    IIC_Send_Byte(MPU6050_ADDR | 0x01);
    IIC_Wait_Ack();
    data = IIC_Read_Byte(0);
    IIC_Stop();
    return data;
}

// 初始化MPU6050
uint8_t MPU6050_Init(void)
{
    delay_ms(100);  // 等待上电稳定

    // 读取WHO_AM_I寄存器验证设备ID
    uint8_t device_id = MPU6050_ReadReg(MPU6050_WHO_AM_I);
    if(device_id != 0x68)
    {
        return 0;  // 设备ID不正确
    }

    // 复位设备
    MPU6050_WriteReg(MPU6050_PWR_MGMT_1, 0x80);
    delay_ms(100);

    // 唤醒设备，选择时钟源
    MPU6050_WriteReg(MPU6050_PWR_MGMT_1, 0x01);

    // 配置加速度计量程为±2g
    MPU6050_WriteReg(MPU6050_ACCEL_CONFIG, 0x00);

    // 配置陀螺仪量程为±250°/s
    MPU6050_WriteReg(MPU6050_GYRO_CONFIG, 0x00);

    // 配置数字低通滤波器
    MPU6050_WriteReg(MPU6050_CONFIG, 0x03);

    // 设置采样率为50Hz
    MPU6050_WriteReg(MPU6050_SMPLRT_DIV, 0x13);

    return 1;  // 初始化成功
}

// 设置加速度量程
void MPU6050_SetAccelRange(MPU6050_AccelRange range)
{
    MPU6050_WriteReg(MPU6050_ACCEL_CONFIG, range);

    // 更新比例因子
    switch(range)
    {
        case MPU6050_ACCEL_RANGE_2G:
            accel_scale = 16384.0f;
            break;
        case MPU6050_ACCEL_RANGE_4G:
            accel_scale = 8192.0f;
            break;
        case MPU6050_ACCEL_RANGE_8G:
            accel_scale = 4096.0f;
            break;
        case MPU6050_ACCEL_RANGE_16G:
            accel_scale = 2048.0f;
            break;
    }
}

// 读取X轴和Y轴加速度
void MPU6050_ReadAccel(float *x, float *y)
{
    uint8_t buffer[6];
    uint16_t temp;

    // 读取6个字节的加速度数据
    IIC_Start();
    IIC_Send_Byte(MPU6050_ADDR);
    IIC_Wait_Ack();
    IIC_Send_Byte(MPU6050_ACCEL_XOUT_H);
    IIC_Wait_Ack();
    IIC_Start();
    IIC_Send_Byte(MPU6050_ADDR | 0x01);
    IIC_Wait_Ack();

    for(int i = 0; i < 6; i++)
    {
        if(i == 5)
            buffer[i] = IIC_Read_Byte(0);  // 最后一个字节发送NACK
        else
            buffer[i] = IIC_Read_Byte(1);  // 发送ACK
    }
    IIC_Stop();

    // 转换X轴加速度
    temp = (buffer[0] << 8) | buffer[1];
    *x = (float)temp / accel_scale;

    // 转换Y轴加速度
    temp = (buffer[2] << 8) | buffer[3];
    *y = (float)temp / accel_scale;
}

// 读取所有轴加速度
void MPU6050_ReadAccelAll(float *x, float *y, float *z)
{
    uint8_t buffer[6];
    uint16_t temp;

    // 读取6个字节的加速度数据
    IIC_Start();
    IIC_Send_Byte(MPU6050_ADDR);
    IIC_Wait_Ack();
    IIC_Send_Byte(MPU6050_ACCEL_XOUT_H);
    IIC_Wait_Ack();
    IIC_Start();
    IIC_Send_Byte(MPU6050_ADDR | 0x01);
    IIC_Wait_Ack();

    for(int i = 0; i < 6; i++)
    {
        if(i == 5)
            buffer[i] = IIC_Read_Byte(0);  // 最后一个字节发送NACK
        else
            buffer[i] = IIC_Read_Byte(1);  // 发送ACK
    }
    IIC_Stop();

    // 转换X轴加速度
    temp = (buffer[0] << 8) | buffer[1];
    *x = (float)temp / accel_scale;

    // 转换Y轴加速度
    temp = (buffer[2] << 8) | buffer[3];
    *y = (float)temp / accel_scale;

    // 转换Z轴加速度
    temp = (buffer[4] << 8) | buffer[5];
    *z = (float)temp / accel_scale;
}

