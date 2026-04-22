#include "iic.h"
#include "delay.h"

void IIC_Init(void)
{
    GPIO_InitTypeDef GPIO_InitStructure;

    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOB, ENABLE);

    GPIO_InitStructure.GPIO_Pin = IIC_SCL_PIN | IIC_SDA_PIN;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_OD;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(IIC_PORT, &GPIO_InitStructure);

    GPIO_SetBits(IIC_PORT, IIC_SCL_PIN | IIC_SDA_PIN);
}

void IIC_Start(void)
{
    IIC_SDA_1(); // 替换 IC_SDA = 1;
    IIC_SCL_1(); // 替换 IC_SCL = 1;
    delay_us(4);
    IIC_SDA_0(); // 替换 IC_SDA = 0;
    delay_us(4);
    IIC_SCL_0(); // 替换 IC_SCL = 0;
}

void IIC_Stop(void)
{
    SDA_OUT();       // 保持不变（已封装为STM32模式）
    IIC_SCL_0();     // 替换 IIC_SCL = 0;
    IIC_SDA_0();     // 替换 IIC_SDA = 0;
    delay_us(4);     // 确保delay_us函数已实现（STM32需单独写）
    IIC_SCL_1();     // 替换 IIC_SCL = 1;
    IIC_SDA_1();     // 替换 IIC_SDA = 1;
    delay_us(4);
}
uint8_t IIC_Wait_Ack(void)
{
    uint8_t ucErrTime = 0;

    SDA_IN();          // 保持不变（已封装为STM32输入模式）
    IIC_SDA_1();       // 替换 IIC_SDA = 1;
    delay_us(1);
    IIC_SCL_1();       // 替换 IIC_SCL = 1;
    delay_us(1);
    while(READ_SDA)    // READ_SDA已封装，无需修改
    {
        ucErrTime++;
        if(ucErrTime > 250)
        {
            IIC_Stop();  // 依赖之前修正的IIC_Stop函数
            return 1;
        }
    }
    IIC_SCL_0();       // 替换 IIC_SCL = 0;
    return 0;
}

void IIC_Ack(void)
{
    IIC_SCL_0();       // 替换 IIC_SCL = 0;
    SDA_OUT();         // 保持不变（已封装）
    IIC_SDA_0();       // 替换 IIC_SDA = 0;
    delay_us(2);
    IIC_SCL_1();       // 替换 IIC_SCL = 1;
    delay_us(2);
    IIC_SCL_0();       // 替换 IIC_SCL = 0;
}

void IIC_NAck(void)
{
    IIC_SCL_0();       // 替换 IIC_SCL = 0;
    SDA_OUT();         // 保持不变（已封装）
    IIC_SDA_1();       // 替换 IIC_SDA = 1;
    delay_us(2);
    IIC_SCL_1();       // 替换 IIC_SCL = 1;
    delay_us(2);
    IIC_SCL_0();       // 替换 IIC_SCL = 0;
}
void IIC_Send_Byte(uint8_t txd)
{
    uint8_t t;
    SDA_OUT();         // 保持不变（已封装为STM32输出模式）
    IIC_SCL_0();       // 替换 IIC_SCL = 0;
    for(t = 0; t < 8; t++)  // 循环发送8位（1字节）
    {
        // 核心：根据位值设置SDA电平（替换原IIC_SDA赋值）
        if((txd & 0x80) >> 7)  // 取最高位，判断是1还是0
        {
            IIC_SDA_1();       // 最高位为1，SDA置高
        }
        else
        {
            IIC_SDA_0();       // 最高位为0，SDA置低
        }
        txd <<= 1;             // 左移一位，准备发送下一位（逻辑不变）
        delay_us(2);
        IIC_SCL_1();           // 替换 IIC_SCL = 1;（时钟拉高，从机读取SDA）
        delay_us(2);
        IIC_SCL_0();           // 替换 IIC_SCL = 0;（时钟拉低，准备下一位）
        delay_us(2);
    }
}



uint8_t IIC_Read_Byte(uint8_t ack)
{
    uint8_t i, receive = 0;
    SDA_IN();          // 保持不变（已封装为STM32的SDA输入模式，用于读取电平）
    
    for(i = 0; i < 8; i++)  // 循环读取8位（1个字节）
    {
        IIC_SCL_0();       // 替换 IIC_SCL = 0;（拉低时钟，准备读取）
        delay_us(2);
        IIC_SCL_1();       // 替换 IIC_SCL = 1;（拉高时钟，从机输出数据到SDA）
        
        receive <<= 1;     // 接收变量左移1位，腾出最低位存新数据（逻辑不变）
        if(READ_SDA)       // READ_SDA已封装，读取SDA电平（1/0）
            receive++;     // 若SDA为1，接收变量最低位置1（等价于 receive |= 1）
        
        delay_us(1);
    }
    
    // 根据ack参数，发送应答/非应答（调用之前修正的函数）
    if(!ack)
        IIC_NAck();        // ack=0 → 发非应答（告诉从机停止发送）
    else
        IIC_Ack();         // ack=1 → 发应答（告诉从机继续发送）
    
    return receive;        // 返回读取到的1字节数据
}
