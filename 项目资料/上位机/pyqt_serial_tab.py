#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
串口助手标签页模块 - PyQt6版本
完全复制原Tkinter版本的界面和功能
"""

import time
import binascii
import serial
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QComboBox, QLineEdit, QTextEdit, QSpinBox, QCheckBox, QRadioButton,
    QButtonGroup, QGroupBox, QSplitter, QMessageBox, QFileDialog,
    QFrame, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QTextCursor, QColor, QPalette


class SerialTab(QWidget):
    """串口助手标签页 - PyQt6版本"""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        # 状态变量
        self.hex_mode = False
        self.repeat_send_timer = QTimer()
        self.repeat_send_timer.timeout.connect(self.repeat_send_data)

        # 创建界面
        self.create_widgets()

    def create_widgets(self):
        """创建界面组件"""
        # 创建主布局
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # 左侧：串口设置和控制
        left_widget = QWidget()
        left_widget.setMaximumWidth(400)
        left_layout = QVBoxLayout(left_widget)
        splitter.addWidget(left_widget)

        # 串口设置区域
        self.create_serial_settings(left_layout)

        # 发送区域
        self.create_send_area(left_layout)

        # 显示设置
        self.create_display_settings(left_layout)

        # 右侧：数据显示区域
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        splitter.addWidget(right_widget)

        # 数据显示区域
        self.create_data_display(right_layout)

        # 设置分割器比例
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

    def create_serial_settings(self, layout):
        """创建串口设置区域"""
        # 串口设置框
        settings_group = QGroupBox("串口配置")
        layout.addWidget(settings_group)
        settings_layout = QVBoxLayout(settings_group)

        # 基本连接设置
        basic_frame = QFrame()
        basic_layout = QGridLayout(basic_frame)
        settings_layout.addWidget(basic_frame)

        # COM端口
        basic_layout.addWidget(QLabel("COM端口:"), 0, 0)
        self.port_combo = QComboBox()
        self.port_combo.setEditable(True)
        basic_layout.addWidget(self.port_combo, 0, 1)
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.refresh_ports)
        basic_layout.addWidget(self.refresh_btn, 0, 2)

        # 波特率设置
        basic_layout.addWidget(QLabel("波特率:"), 1, 0)
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.setEditable(True)
        baudrates = ["1200", "2400", "4800", "9600", "19200", "38400",
                    "57600", "115200", "230400", "460800", "921600"]
        self.baudrate_combo.addItems(baudrates)
        self.baudrate_combo.setCurrentText("9600")
        basic_layout.addWidget(self.baudrate_combo, 1, 1)
        self.custom_baud_btn = QPushButton("自定义")
        self.custom_baud_btn.clicked.connect(self.custom_baudrate)
        basic_layout.addWidget(self.custom_baud_btn, 1, 2)

        # 高级串口参数
        advanced_group = QGroupBox("高级参数")
        settings_layout.addWidget(advanced_group)
        advanced_layout = QGridLayout(advanced_group)

        # 数据位
        advanced_layout.addWidget(QLabel("数据位:"), 0, 0)
        self.databits_combo = QComboBox()
        self.databits_combo.addItems(["5", "6", "7", "8"])
        self.databits_combo.setCurrentText("8")
        advanced_layout.addWidget(self.databits_combo, 0, 1)

        # 停止位
        advanced_layout.addWidget(QLabel("停止位:"), 0, 2)
        self.stopbits_combo = QComboBox()
        self.stopbits_combo.addItems(["1", "1.5", "2"])
        self.stopbits_combo.setCurrentText("1")
        advanced_layout.addWidget(self.stopbits_combo, 0, 3)

        # 校验位
        advanced_layout.addWidget(QLabel("校验位:"), 1, 0)
        self.parity_combo = QComboBox()
        self.parity_combo.addItems(["None", "Even", "Odd", "Mark", "Space"])
        self.parity_combo.setCurrentText("None")
        advanced_layout.addWidget(self.parity_combo, 1, 1)

        # 流控制
        advanced_layout.addWidget(QLabel("流控制:"), 1, 2)
        self.flowcontrol_combo = QComboBox()
        self.flowcontrol_combo.addItems(["None", "XON/XOFF", "RTS/CTS"])
        self.flowcontrol_combo.setCurrentText("None")
        advanced_layout.addWidget(self.flowcontrol_combo, 1, 3)

        # 超时设置
        timeout_frame = QFrame()
        timeout_layout = QHBoxLayout(timeout_frame)
        settings_layout.addWidget(timeout_frame)

        timeout_layout.addWidget(QLabel("超时设置 (秒):"))
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(1, 100)
        self.timeout_spin.setValue(1)
        timeout_layout.addWidget(self.timeout_spin)

        # 连接控制
        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        settings_layout.addWidget(control_frame)

        self.connect_btn = QPushButton("连接串口")
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
        """)
        self.connect_btn.clicked.connect(self.toggle_connection)
        control_layout.addWidget(self.connect_btn)

        self.status_label = QLabel("状态: 未连接")
        self.status_label.setStyleSheet("color: #666666;")
        control_layout.addWidget(self.status_label)

        # 初始化端口列表
        self.refresh_ports()

    def create_send_area(self, layout):
        """创建发送区域"""
        # 发送区域
        send_group = QGroupBox("数据发送")
        layout.addWidget(send_group)
        send_layout = QVBoxLayout(send_group)

        # 发送格式选择
        format_frame = QFrame()
        format_layout = QHBoxLayout(format_frame)
        send_layout.addWidget(format_frame)

        format_layout.addWidget(QLabel("发送格式:"))
        self.send_format_group = QButtonGroup()
        self.ascii_radio = QRadioButton("ASCII")
        self.ascii_radio.setChecked(True)
        self.hex_radio = QRadioButton("HEX")
        self.send_format_group.addButton(self.ascii_radio, 0)
        self.send_format_group.addButton(self.hex_radio, 1)
        format_layout.addWidget(self.ascii_radio)
        format_layout.addWidget(self.hex_radio)

        # 发送选项
        options_frame = QFrame()
        options_layout = QHBoxLayout(options_frame)
        send_layout.addWidget(options_frame)

        self.add_newline_check = QCheckBox("添加换行符(\\r\\n)")
        self.add_newline_check.setChecked(True)
        options_layout.addWidget(self.add_newline_check)

        self.repeat_send_check = QCheckBox("重复发送")
        self.repeat_send_check.toggled.connect(self.toggle_repeat_send)
        options_layout.addWidget(self.repeat_send_check)

        options_layout.addWidget(QLabel("间隔(ms):"))
        self.repeat_interval_spin = QSpinBox()
        self.repeat_interval_spin.setRange(100, 10000)
        self.repeat_interval_spin.setValue(1000)
        options_layout.addWidget(self.repeat_interval_spin)

        # 发送数据输入
        send_layout.addWidget(QLabel("发送数据:"))
        text_frame = QFrame()
        text_layout = QHBoxLayout(text_frame)
        send_layout.addWidget(text_frame)

        self.send_entry = QLineEdit()
        self.send_entry.setFont(QFont("Consolas", 10))
        self.send_entry.returnPressed.connect(self.send_data)
        text_layout.addWidget(self.send_entry)

        self.clear_send_btn = QPushButton("清空")
        self.clear_send_btn.clicked.connect(lambda: self.send_entry.clear())
        self.clear_send_btn.setMaximumWidth(80)
        text_layout.addWidget(self.clear_send_btn)

        # 发送按钮
        send_btn_frame = QFrame()
        send_btn_layout = QHBoxLayout(send_btn_frame)
        send_layout.addWidget(send_btn_frame)

        self.send_btn = QPushButton("发送")
        self.send_btn.clicked.connect(self.send_data)
        send_btn_layout.addWidget(self.send_btn)

        self.repeat_btn = QPushButton("开始重复")
        self.repeat_btn.clicked.connect(self.toggle_repeat_send)
        send_btn_layout.addWidget(self.repeat_btn)

    def create_display_settings(self, layout):
        """创建显示设置"""
        # 显示设置
        display_group = QGroupBox("显示设置")
        layout.addWidget(display_group)
        display_layout = QVBoxLayout(display_group)

        # 显示格式
        format_display_frame = QFrame()
        format_display_layout = QHBoxLayout(format_display_frame)
        display_layout.addWidget(format_display_frame)

        format_display_layout.addWidget(QLabel("接收显示:"))
        self.display_format_group = QButtonGroup()
        self.ascii_only_radio = QRadioButton("仅ASCII")
        self.hex_only_radio = QRadioButton("仅HEX")
        self.both_radio = QRadioButton("都显示")
        self.both_radio.setChecked(True)
        self.display_format_group.addButton(self.ascii_only_radio, 0)
        self.display_format_group.addButton(self.hex_only_radio, 1)
        self.display_format_group.addButton(self.both_radio, 2)
        format_display_layout.addWidget(self.ascii_only_radio)
        format_display_layout.addWidget(self.hex_only_radio)
        format_display_layout.addWidget(self.both_radio)

        # 显示选项
        self.auto_scroll_check = QCheckBox("自动滚动")
        self.auto_scroll_check.setChecked(True)
        display_layout.addWidget(self.auto_scroll_check)

        self.show_timestamp_check = QCheckBox("显示时间戳")
        self.show_timestamp_check.setChecked(True)
        display_layout.addWidget(self.show_timestamp_check)

        self.show_parsed_check = QCheckBox("显示解析数据")
        self.show_parsed_check.setChecked(True)
        display_layout.addWidget(self.show_parsed_check)

        # 操作按钮
        btn_frame = QFrame()
        btn_layout = QHBoxLayout(btn_frame)
        display_layout.addWidget(btn_frame)

        self.save_log_btn = QPushButton("保存日志")
        self.save_log_btn.clicked.connect(self.save_log)
        btn_layout.addWidget(self.save_log_btn)

        self.clear_display_btn = QPushButton("清空显示")
        self.clear_display_btn.clicked.connect(self.clear_display)
        btn_layout.addWidget(self.clear_display_btn)

        self.show_stats_btn = QPushButton("统计信息")
        self.show_stats_btn.clicked.connect(self.show_statistics)
        btn_layout.addWidget(self.show_stats_btn)

    def create_data_display(self, layout):
        """创建数据显示区域"""
        # 数据显示框
        display_group = QGroupBox("数据接收")
        layout.addWidget(display_group)
        display_layout = QVBoxLayout(display_group)

        # 接收数据显示区域
        self.receive_text = QTextEdit()
        self.receive_text.setFont(QFont("Consolas", 10))
        self.receive_text.setReadOnly(True)
        display_layout.addWidget(self.receive_text)

    def refresh_ports(self):
        """刷新串口列表"""
        ports = self.main_window.get_available_ports()
        self.port_combo.clear()
        self.port_combo.addItems(ports)

        # 如果COM7在列表中，优先选择COM7
        if "COM7" in ports:
            self.port_combo.setCurrentText("COM7")

    def toggle_connection(self):
        """切换串口连接状态"""
        port = self.port_combo.currentText()
        if not port:
            QMessageBox.warning(self, "错误", "请选择COM端口")
            return

        try:
            baudrate = int(self.baudrate_combo.currentText())
            databits = int(self.databits_combo.currentText())
            stopbits = float(self.stopbits_combo.currentText())
            parity = self.parity_combo.currentText().upper()
            timeout = self.timeout_spin.value()

            if self.main_window.is_connected():
                # 断开连接
                self.main_window.disconnect_serial()
                self.connect_btn.setText("连接串口")
                self.connect_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #2196F3;
                        color: white;
                        padding: 8px 16px;
                        border: none;
                        border-radius: 4px;
                    }
                """)
                self.status_label.setText("状态: 未连接")
                self.status_label.setStyleSheet("color: #666666;")
                self.add_message("串口已断开")
            else:
                # 建立连接
                if self.main_window.connect_serial(port, baudrate):
                    self.connect_btn.setText("断开连接")
                    self.connect_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #F44336;
                            color: white;
                            padding: 8px 16px;
                        border: none;
                        border-radius: 4px;
                        }
                    """)
                    self.status_label.setText(f"状态: 已连接 {port}")
                    self.status_label.setStyleSheet("color: #27AE60;")
                    config_info = f"端口:{port} 波特率:{baudrate} 数据位:{databits} 校验:{parity} 停止位:{stopbits}"
                    self.add_message(f"已连接 ({config_info})")

                    # 连接成功后发送"CONNECT"命令触发STM32显示"on"
                    time.sleep(0.1)  # 等待100ms确保连接稳定
                    self.main_window.send_serial_data("CONNECT\n")
                else:
                    self.status_label.setText("状态: 连接失败")
                    self.status_label.setStyleSheet("color: #E74C3C;")
                    QMessageBox.critical(self, "错误", f"无法连接到 {port}")

        except ValueError as e:
            QMessageBox.critical(self, "错误", f"参数错误: {e}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"连接失败: {e}")

    def send_data(self):
        """发送数据"""
        data_str = self.send_entry.text().strip()
        if not data_str:
            return

        try:
            # 判断发送格式
            if self.hex_radio.isChecked():
                # HEX格式
                data = bytes.fromhex(data_str.replace('0x', '').replace(' ', ''))
            else:
                # ASCII格式
                data = data_str.encode('utf-8')
                if self.add_newline_check.isChecked():
                    data += b'\r\n'

            success = self.main_window.send_serial_data(data)
            if success:
                timestamp = datetime.now().strftime("%H:%M:%S")
                self.add_message(f"[{timestamp}] TX: {data_str}")
                self.send_entry.clear()
            else:
                self.add_message("发送失败", "error")

        except Exception as e:
            self.add_message(f"发送错误: {e}", "error")

    def add_message(self, message, msg_type="data"):
        """添加消息到显示区域"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        # 根据消息类型设置颜色
        color = "#000000"  # 默认黑色
        if msg_type == "error":
            color = "#CC0000"
        elif msg_type == "hex":
            color = "#0066CC"
        elif msg_type == "parsed":
            color = "#009900"
        elif msg_type == "timestamp":
            color = "#666666"

        # 插入消息
        cursor = self.receive_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertHtml(f'<span style="color: #{color};">[{timestamp}] {message}</span><br>')

        # 自动滚动到底部
        if self.auto_scroll_check.isChecked():
            self.receive_text.verticalScrollBar().setValue(self.receive_text.verticalScrollBar().maximum())

        # 限制显示行数
        if self.receive_text.document().blockCount() > 1000:
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
            cursor.removeSelectedText()

    def update_display(self, parsed_data, timestamp):
        """更新数据显示"""
        time_str = timestamp.strftime("%H:%M:%S") if timestamp else datetime.now().strftime("%H:%M:%S")

        # 原始数据显示
        raw_data = parsed_data.get('raw_data', '')

        if self.hex_only_radio.isChecked():
            # 仅显示HEX
            if len(raw_data) % 2 == 0:
                hex_formatted = ' '.join([raw_data[i:i+2] for i in range(0, len(raw_data), 2)])
                self.add_message(f"RX: {hex_formatted.upper()}", "hex")
        elif self.ascii_only_radio.isChecked():
            # 仅显示ASCII
            try:
                if len(raw_data) % 2 == 0:
                    data_bytes = bytes.fromhex(raw_data)
                    ascii_display = data_bytes.decode('ascii', errors='ignore')
                    printable_ascii = ''.join([c if c.isprintable() else '.' for c in ascii_display])
                    self.add_message(f"RX: {printable_ascii}")
                else:
                    self.add_message(f"RX: {raw_data}")
            except:
                self.add_message(f"RX: {raw_data}")
        else:  # Both
            # 显示HEX和ASCII格式
            if len(raw_data) % 2 == 0:
                data_bytes = bytes.fromhex(raw_data)
                hex_formatted = ' '.join([raw_data[i:i+2] for i in range(0, len(raw_data), 2)])
                ascii_display = data_bytes.decode('ascii', errors='ignore')
                printable_ascii = ''.join([c if c.isprintable() else '.' for c in ascii_display])
                self.add_message(f"RX: HEX[{hex_formatted.upper()}] ASCII[{printable_ascii}]")
            else:
                self.add_message(f"RX: {raw_data}")

        # 解析数据显示
        if self.show_parsed_check.isChecked():
            temp = parsed_data.get('temperature', 0)
            heart = parsed_data.get('heart_rate', 0)
            accel_x = parsed_data.get('accel_x', 0)
            accel_y = parsed_data.get('accel_y', 0)
            accel_z = parsed_data.get('accel_z', 0)
            movement = parsed_data.get('movement_index', 0)

            parsed_msg = (f"解析: 体温={temp:.1f}°C, 心率={heart}bpm, "
                         f"加速度X={accel_x:.0f}, Y={accel_y:.0f}, Z={accel_z:.0f}, 体动={movement}")
            self.add_message(parsed_msg, "parsed")

    def update_connection_status(self, connected):
        """更新连接状态显示"""
        if connected:
            self.connect_btn.setText("断开连接")
            self.connect_btn.setStyleSheet("""
                QPushButton {
                    background-color: #F44336;
                    color: white;
                    padding: 8px 16px;
                    border: none;
                    border-radius: 4px;
                }
            """)
            current_port = self.port_combo.currentText()
            self.status_label.setText(f"状态: 已连接 {current_port}")
            self.status_label.setStyleSheet("color: #27AE60;")
        else:
            self.connect_btn.setText("连接串口")
            self.connect_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    padding: 8px 16px;
                    border: none;
                    border-radius: 4px;
                }
            """)
            self.status_label.setText("状态: 未连接")
            self.status_label.setStyleSheet("color: #666666;")
            self.repeat_send_check.setChecked(False)
            self.stop_repeat_send()

    def toggle_repeat_send(self):
        """切换重复发送"""
        if self.repeat_send_check.isChecked():
            self.start_repeat_send()
        else:
            self.stop_repeat_send()

    def start_repeat_send(self):
        """开始重复发送"""
        if not self.main_window.is_connected():
            QMessageBox.warning(self, "警告", "请先连接串口")
            self.repeat_send_check.setChecked(False)
            return

        interval = self.repeat_interval_spin.value()
        self.repeat_send_timer.start(interval)
        self.repeat_btn.setText("停止重复")

    def stop_repeat_send(self):
        """停止重复发送"""
        self.repeat_send_timer.stop()
        self.repeat_btn.setText("开始重复")

    def repeat_send_data(self):
        """重复发送数据"""
        if self.repeat_send_check.isChecked() and self.main_window.is_connected():
            self.send_data()

    def custom_baudrate(self):
        """自定义波特率"""
        from PyQt6.QtWidgets import QInputDialog

        baud, ok = QInputDialog.getText(self, "自定义波特率", "输入自定义波特率:")
        if ok:
            try:
                baud = int(baud)
                if 300 <= baud <= 3000000:
                    if str(baud) not in [self.baudrate_combo.itemText(i) for i in range(self.baudrate_combo.count())]:
                        self.baudrate_combo.addItem(str(baud))
                    self.baudrate_combo.setCurrentText(str(baud))
                else:
                    QMessageBox.warning(self, "错误", "波特率范围: 300 - 3000000")
            except ValueError:
                QMessageBox.warning(self, "错误", "请输入有效的数字")

    def clear_display(self):
        """清空显示"""
        self.receive_text.clear()

    def save_log(self):
        """保存日志"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "保存串口日志",
            f"serial_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "文本文件 (*.txt);;所有文件 (*.*)"
        )

        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.receive_text.toPlainText())
                QMessageBox.information(self, "成功", f"日志已保存到: {filename}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {e}")

    def show_statistics(self):
        """显示统计信息"""
        content = self.receive_text.toPlainText()
        lines = content.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]

        total_chars = len(content)
        total_lines = len(non_empty_lines)
        rx_lines = len([line for line in non_empty_lines if 'RX:' in line])
        tx_lines = len([line for line in non_empty_lines if 'TX:' in line])
        parsed_lines = len([line for line in non_empty_lines if '解析:' in line])

        stats = f"""串口统计信息

总字符数: {total_chars}
总行数: {total_lines}
接收行数: {rx_lines}
发送行数: {tx_lines}
解析行数: {parsed_lines}

连接状态: {'已连接' if self.main_window.is_connected() else '未连接'}
当前端口: {self.port_combo.currentText()}
当前波特率: {self.baudrate_combo.currentText()}
"""

        QMessageBox.information(self, "统计信息", stats)