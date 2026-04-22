#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
健康监测系统 - 业务逻辑控制器
负责处理所有业务逻辑，包括数据处理、通信、报警等
"""

import serial
import serial.tools.list_ports
import threading
import time
from datetime import datetime
from collections import deque
import json
import os
from typing import Optional, Callable, Dict, Any, List


class MonitorController:
    """监测控制器 - 处理所有业务逻辑"""

    def __init__(self):
        # 串口相关
        self.serial_port: Optional[serial.Serial] = None
        self.is_connected = False
        self.receive_thread: Optional[threading.Thread] = None
        self.stop_receive = threading.Event()

        # 数据缓存
        self.data_buffer = deque(maxlen=100)  # 最近100条数据
        self.current_data = {
            'temperature': 0.0,
            'heart_rate': 0,
            'accel_x': 0.0,
            'accel_y': 0.0,
            'timestamp': None
        }

        # 记录上次的值
        self.last_temp = 0.0
        self.last_heart = 0

        # 报警设置
        self.alarm_settings = {
            'temp_min': 36.0,
            'temp_max': 37.5,
            'heart_min': 60,
            'heart_max': 120
        }

        # 回调函数
        self.callbacks: Dict[str, List[Callable]] = {
            'data_received': [],
            'connection_changed': [],
            'alarm_triggered': [],
            'error_occurred': []
        }

        # 统计信息
        self.statistics = {
            'total_received': 0,
            'error_count': 0,
            'alarm_count': 0,
            'connection_time': 0,
            'start_time': time.time()
        }

        # 数据记录
        self.data_history: List[Dict] = []
        self.max_history = 10000  # 最多保存10000条历史记录

        # 温度平滑处理
        self.temp_buffer = deque(maxlen=5)  # 用于温度平滑的缓冲区
        self.last_temp = 36.5  # 上一次的温度值

    def register_callback(self, event: str, callback: Callable):
        """注册回调函数"""
        if event in self.callbacks:
            self.callbacks[event].append(callback)

    def unregister_callback(self, event: str, callback: Callable):
        """取消注册回调函数"""
        if event in self.callbacks and callback in self.callbacks[event]:
            self.callbacks[event].remove(callback)

    def _trigger_callback(self, event: str, *args, **kwargs):
        """触发回调函数"""
        for callback in self.callbacks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception as e:
                print(f"回调函数执行错误: {e}")

    def get_available_ports(self) -> List[str]:
        """获取可用的串口列表"""
        ports = []
        # ��加COM4到COM9的固定选项
        for i in range(4, 10):
            ports.append(f"COM{i}")

        # 扫描实际可用的串口
        try:
            for port in serial.tools.list_ports.comports():
                if port.device not in ports:
                    ports.append(port.device)
        except:
            pass

        return ports

    def connect_serial(self, port: str, baudrate: int = 9600,
                      databits: int = 8, parity: str = "N",
                      stopbits: int = 1) -> bool:
        """连接串口"""
        try:
            if self.is_connected:
                self.disconnect_serial()

            # 转换参数
            bytesize_map = {5: serial.FIVEBITS, 6: serial.SIXBITS,
                           7: serial.SEVENBITS, 8: serial.EIGHTBITS}
            parity_map = {"N": serial.PARITY_NONE, "E": serial.PARITY_EVEN,
                         "O": serial.PARITY_ODD}
            stopbits_map = {1: serial.STOPBITS_ONE, 2: serial.STOPBITS_TWO}

            self.serial_port = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=bytesize_map.get(databits, serial.EIGHTBITS),
                parity=parity_map.get(parity.upper(), serial.PARITY_NONE),
                stopbits=stopbits_map.get(stopbits, serial.STOPBITS_ONE),
                timeout=1
            )

            self.is_connected = True
            self.stop_receive.clear()

            # 启动接收线程
            self.receive_thread = threading.Thread(target=self._receive_data_thread)
            self.receive_thread.daemon = True
            self.receive_thread.start()

            # 更新统计信息
            self.statistics['connection_time'] = time.time()

            self._trigger_callback('connection_changed', True)
            return True

        except Exception as e:
            self._trigger_callback('error_occurred', f"连接串口失败: {str(e)}")
            return False

    def disconnect_serial(self):
        """断开串口连接"""
        self.stop_receive.set()

        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(timeout=1)

        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()

        self.is_connected = False
        self._trigger_callback('connection_changed', False)

    def _receive_data_thread(self):
        """数据接收线程"""
        line_buffer = ''

        while not self.stop_receive.is_set() and self.is_connected:
            try:
                if self.serial_port.in_waiting > 0:
                    # 读取所有可用数据
                    data = self.serial_port.read(self.serial_port.in_waiting)

                    # 尝试解码为文本
                    try:
                        text = data.decode('ascii', errors='ignore')
                        line_buffer += text

                        # 处理完整行（以换行符分隔）
                        while '\n' in line_buffer or '\r' in line_buffer:
                            # 优先使用\n作为分隔符
                            if '\n' in line_buffer:
                                line, line_buffer = line_buffer.split('\n', 1)
                            else:
                                line, line_buffer = line_buffer.split('\r', 1)

                            line = line.strip()
                            if line:
                                # 解析文本格式的数据
                                self._parse_text_data(line)
                    except:
                        # 如果解码失败，直接将原始数据作为一行处理
                        self._parse_text_data(str(data))

                else:
                    time.sleep(0.01)

            except Exception as e:
                self.statistics['error_count'] += 1
                self._trigger_callback('error_occurred', f"接收数据错误: {str(e)}")
                break

    def _parse_text_data(self, line: str):
        """解析文本格式的数据"""
        try:
            # 解析各种可能的格式
            # 格式1: "T:36.5,H:75"
            if 'T:' in line and 'H:' in line:
                parts = line.split(',')
                temp = None
                heart = None

                for part in parts:
                    if 'T:' in part or 't:' in part:
                        temp = float(part.split(':')[1].strip())
                    elif 'H:' in part or 'h:' in part:
                        heart = float(part.split(':')[1].strip())

                if temp is not None or heart is not None:
                    # 生成模拟数据
                    self._generate_data_with_values(temp, heart)
                    return

            # 格式2: "36.5,75"
            elif ',' in line and line.count(',') == 1:
                try:
                    values = line.split(',')
                    temp = float(values[0].strip())
                    heart = float(values[1].strip())
                    self._generate_data_with_values(temp, heart)
                    return
                except:
                    pass

            # 格式3: 单独的温度或心率
            elif line.replace('.', '').replace('-', '').isdigit():
                try:
                    value = float(line)
                    # 如果是温度范围，作为温度处理
                    if 30 <= value <= 45:
                        self._generate_data_with_values(value, None)
                    # 如果是心率范围
                    elif 40 <= value <= 200:
                        self._generate_data_with_values(None, value)
                except:
                    pass

            # 其他格式作为调试信息处理
            self._trigger_callback('data_received', {
                'raw_data': line,
                'timestamp': datetime.now()
            })

        except Exception as e:
            self.statistics['error_count'] += 1

    def _generate_data_with_values(self, temperature=None, heart_rate=None):
        """使用指定的温度和心率生成数据"""
        import random

        # 如果没有提供温度，使用上次值或生成
        if temperature is None:
            if self.last_temp > 0:
                temperature = self.last_temp
            else:
                temperature = 36.0 + random.random() * 2.0  # 36-38度

        # 如果没有提供心率，使用上次值或生成
        if heart_rate is None:
            if self.last_heart > 0:
                heart_rate = self.last_heart
            else:
                heart_rate = 60 + random.randint(10, 40)  # 60-100

        # 限制范围
        temperature = max(30, min(45, temperature))
        heart_rate = max(40, min(200, heart_rate))

        # 记录上次值
        self.last_temp = temperature
        self.last_heart = heart_rate

        # 生成加速度数据（模拟）
        accel_x = random.uniform(-0.5, 0.5)
        accel_y = random.uniform(-0.5, 0.5)

        # 更新当前数据
        self.current_data.update({
            'temperature': temperature,
            'heart_rate': heart_rate,
            'accel_x': accel_x,
            'accel_y': accel_y,
            'timestamp': datetime.now()
        })

        # 添加到缓冲区
        self.data_buffer.append(self.current_data.copy())

        # 添加到历史记录
        self.data_history.append(self.current_data.copy())
        if len(self.data_history) > self.max_history:
            self.data_history.pop(0)

        # 更新统计
        self.statistics['total_received'] += 1

        # 检查报警
        self._check_alarms()

        # 触发数据接收回调
        self._trigger_callback('data_received', self.current_data)

    def _parse_modbus_response(self, response: bytes):
        """解析Modbus响应"""
        try:
            # 验证CRC（简化版本）
            if len(response) != 13:
                return

            # 提取数据
            temp_raw = (response[3] << 8) | response[4]
            heart_raw = (response[5] << 8) | response[6]
            accel_x_raw = (response[7] << 8) | response[8]
            accel_y_raw = (response[9] << 8) | response[10]

            # 转换为实际值
            raw_temp = temp_raw / 10.0  # 温度，放大10倍
            heart_rate = heart_raw
            accel_x = accel_x_raw / 100.0  # 加速度，放大100倍
            accel_y = accel_y_raw / 100.0

            # 温度平滑处理
            self.temp_buffer.append(raw_temp)
            if len(self.temp_buffer) >= 3:
                # 使用移动平均进行平滑
                temperature = sum(self.temp_buffer) / len(self.temp_buffer)
                # 限制相邻点差值不超过0.2度
                if self.last_temp > 0:
                    max_change = 0.2
                    if temperature > self.last_temp + max_change:
                        temperature = self.last_temp + max_change
                    elif temperature < self.last_temp - max_change:
                        temperature = self.last_temp - max_change
                self.last_temp = temperature
            else:
                temperature = self.last_temp if self.last_temp > 0 else 36.5

            # 更新当前数据
            self.current_data.update({
                'temperature': temperature,
                'heart_rate': heart_rate,
                'accel_x': accel_x,
                'accel_y': accel_y,
                'timestamp': datetime.now()
            })

            # 添加到缓冲区
            self.data_buffer.append(self.current_data.copy())

            # 添加到历史记录
            self.data_history.append(self.current_data.copy())
            if len(self.data_history) > self.max_history:
                self.data_history.pop(0)

            # 更新统计
            self.statistics['total_received'] += 1

            # 检查报警
            self._check_alarms()

            # 触发数据接收回调
            self._trigger_callback('data_received', self.current_data)

        except Exception as e:
            self.statistics['error_count'] += 1
            self._trigger_callback('error_occurred', f"解析数据错误: {str(e)}")

    def _check_alarms(self):
        """检查报警条件"""
        temp = self.current_data['temperature']
        heart = self.current_data['heart_rate']

        alarms = []

        if temp < self.alarm_settings['temp_min']:
            alarms.append(f"温度过低: {temp:.1f}°C")
        elif temp > self.alarm_settings['temp_max']:
            alarms.append(f"温度过高: {temp:.1f}°C")

        if heart < self.alarm_settings['heart_min']:
            alarms.append(f"心率过慢: {heart} bpm")
        elif heart > self.alarm_settings['heart_max']:
            alarms.append(f"心率过快: {heart} bpm")

        if alarms:
            self.statistics['alarm_count'] += 1
            self._trigger_callback('alarm_triggered', alarms)

    def send_data(self, data: str) -> bool:
        """发送数据"""
        if not self.is_connected or not self.serial_port:
            return False

        try:
            self.serial_port.write(data.encode('utf-8'))
            return True
        except Exception as e:
            self._trigger_callback('error_occurred', f"发送数据失败: {str(e)}")
            return False

    def update_alarm_settings(self, settings: Dict[str, float]):
        """更新报警设置"""
        self.alarm_settings.update(settings)

    def get_current_data(self) -> Dict[str, Any]:
        """获取当前数据"""
        return self.current_data.copy()

    def get_data_buffer(self) -> List[Dict]:
        """获取数据缓冲区"""
        return list(self.data_buffer)

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self.statistics.copy()
        if self.is_connected:
            stats['connected_duration'] = time.time() - self.statistics['connection_time']
        else:
            stats['connected_duration'] = 0
        return stats

    def save_data_to_file(self, filename: str) -> bool:
        """保存数据到文件"""
        try:
            data = {
                'current_data': self.current_data,
                'data_history': self.data_history,
                'statistics': self.get_statistics(),
                'alarm_settings': self.alarm_settings,
                'save_time': datetime.now().isoformat()
            }

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)

            return True
        except Exception as e:
            self._trigger_callback('error_occurred', f"保存数据失败: {str(e)}")
            return False

    def load_data_from_file(self, filename: str) -> bool:
        """从文件加载数据"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.current_data = data.get('current_data', self.current_data)
            self.data_history = data.get('data_history', [])

            # 更新缓冲区
            self.data_buffer.clear()
            for item in self.data_history[-100:]:  # 只加载最近100条
                self.data_buffer.append(item)

            return True
        except Exception as e:
            self._trigger_callback('error_occurred', f"加载数据失败: {str(e)}")
            return False

    def clear_data(self):
        """清空所有数据"""
        self.data_buffer.clear()
        self.data_history.clear()
        self.current_data = {
            'temperature': 0.0,
            'heart_rate': 0,
            'accel_x': 0.0,
            'accel_y': 0.0,
            'timestamp': None
        }

        # 重置统计信息
        self.statistics.update({
            'total_received': 0,
            'error_count': 0,
            'alarm_count': 0,
            'connection_time': 0,
            'start_time': time.time()
        })

    def generate_health_advice(self, data: Dict[str, Any]) -> List[str]:
        """生成健康建议"""
        advice = []
        temp = data.get('temperature', 0)
        heart = data.get('heart_rate', 0)

        # 温度相关建议
        if temp > 37.5:
            advice.append("体温偏高，建议多喝水，注意休息")
        elif temp < 36.0:
            advice.append("体温偏低，注意保暖")

        # 心率相关建议
        if heart > 120:
            advice.append("心率过快，建议深呼吸放松")
        elif heart < 60:
            advice.append("心率偏慢，如无不适属正常现象")

        # 正常状态建议
        if not advice:
            advice.append("各项指标正常，继续保持健康生活方式")

        return advice

    def __del__(self):
        """析构函数，确保资源释放"""
        self.disconnect_serial()