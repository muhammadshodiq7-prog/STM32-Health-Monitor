#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
健康监测系统主窗口 - PyQt6版本
完全复制原Tkinter版本的界面和功能
"""

import sys
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QGroupBox, QFrame,
    QMessageBox, QFileDialog, QSpinBox, QComboBox, QCheckBox,
    QTextEdit, QScroller, QSplitter, QStatusBar, QMenuBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon, QPixmap

# 导入控制器
from monitor_controller import MonitorController

# 导入标签页组件
from .pyqt_serial_tab import SerialTab
from .pyqt_monitor_tab import MonitorTab


class HealthMonitorApp(QMainWindow):
    """健康监测应用主窗口 - PyQt6版本"""

    def __init__(self):
        super().__init__()

        # 设置matplotlib后端
        import matplotlib
        matplotlib.use('Qt5Agg')

        # 初始化控制器
        self.controller = MonitorController()

        # 设置窗口属性
        self.setWindowTitle("健康监测系统")
        self.setGeometry(100, 100, 1200, 800)

        # 设置窗口最小大小
        self.setMinimumSize(800, 600)

        # 设置样式
        self.setup_styles()

        # 创建界面
        self.setup_ui()

        # 设置回调
        self.setup_callbacks()

        # 设置状态栏
        self.setup_statusbar()

        # 立即更新窗口
        self.update()

    def setup_styles(self):
        """设置界面样式 - 复制原版样式"""
        # 设置应用程序调色板
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
        self.setPalette(palette)

        # 设置全局样式表
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QTabWidget::pane {
                border: 1px solid #c0c0c0;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #e1e1e1;
                border: 1px solid #c0c0c0;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom-color: white;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 6px 12px;
                background-color: #f8f8f8;
            }
            QPushButton:hover {
                background-color: #e8e8e8;
                border-color: #aaaaaa;
            }
            QPushButton:pressed {
                background-color: #d8d8d8;
            }
        """)

    def setup_ui(self):
        """设置用户界面 - 完全复制原版布局"""
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 创建标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)

        # 创建串口助手标签页
        self.serial_tab = SerialTab(self)
        self.tab_widget.addTab(self.serial_tab, "串口助手")

        # 创建数据监测标签页
        self.monitor_tab = MonitorTab(self)
        self.tab_widget.addTab(self.monitor_tab, "可视化界面")

        # 添加到主布局
        main_layout.addWidget(self.tab_widget)

    def setup_statusbar(self):
        """设置状态栏"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("就绪")

    def setup_callbacks(self):
        """设置回调函数"""
        # 注册控制器回调
        self.controller.register_callback('data_received', self.on_data_received)
        self.controller.register_callback('connection_changed', self.on_connection_changed)
        self.controller.register_callback('alarm_triggered', self.on_alarm_triggered)
        self.controller.register_callback('error_occurred', self.on_error_occurred)

    # 数据处理方法
    @pyqtSlot(dict)
    def on_data_received(self, data):
        """处理接收到的数据"""
        # 更新监测标签页
        self.monitor_tab.update_display(data)
        # 更新串口标签页
        if hasattr(self.serial_tab, 'update_display'):
            parsed_data = {
                'temperature': data.get('temperature', 0),
                'heart_rate': data.get('heart_rate', 0),
                'accel_x': data.get('accel_x', 0),
                'accel_y': data.get('accel_y', 0),
                'accel_z': data.get('accel_z', 0),
                'movement_index': data.get('movement_index', 0),
                'raw_data': data.get('raw_data', '')
            }
            self.serial_tab.update_display(parsed_data, data.get('timestamp'))

    @pyqtSlot(bool)
    def on_connection_changed(self, connected):
        """处理连接状态改变"""
        self.serial_tab.update_connection_status(connected)
        status = "已连接" if connected else "未连接"
        self.statusbar.showMessage(f"串口状态: {status}")

    @pyqtSlot(list)
    def on_alarm_triggered(self, alarms):
        """处理报警"""
        for alarm in alarms:
            self.monitor_tab.add_alarm_message(f"⚠️ {alarm}")

    @pyqtSlot(str)
    def on_error_occurred(self, error_msg):
        """处理错误"""
        self.statusbar.showMessage(f"错误: {error_msg}")
        if hasattr(self.serial_tab, 'add_message'):
            self.serial_tab.add_message(f"❌ {error_msg}")
        else:
            print(f"Error: {error_msg}")

    # 串口控制方法（供SerialTab调用）
    def connect_serial(self, port, baudrate=9600):
        """连接串口"""
        return self.controller.connect_serial(port, baudrate)

    def disconnect_serial(self):
        """断开串口连接"""
        self.controller.disconnect_serial()

    def send_serial_data(self, data):
        """发送串口数据"""
        return self.controller.send_data(data)

    def get_available_ports(self):
        """获取可用串口列表"""
        return self.controller.get_available_ports()

    def is_connected(self):
        """检查是否已连接"""
        return self.controller.is_connected

    # 数据管理方法
    def save_data(self):
        """保存数据"""
        from datetime import datetime
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "保存数据",
            f"health_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON文件 (*.json);;所有文件 (*.*)"
        )

        if filename:
            if self.controller.save_data_to_file(filename):
                QMessageBox.information(self, "成功", f"数据已保存到: {filename}")
            else:
                QMessageBox.critical(self, "错误", "保存数据失败")

    def load_data(self):
        """加载数据"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "加载数据",
            "",
            "JSON文件 (*.json);;所有文件 (*.*)"
        )

        if filename:
            if self.controller.load_data_from_file(filename):
                QMessageBox.information(self, "成功", "数据加载成功")
                # 更新显示
                current_data = self.controller.get_current_data()
                self.monitor_tab.update_display(current_data)
            else:
                QMessageBox.critical(self, "错误", "加载数据失败")

    def generate_health_advice(self):
        """生成健康建议"""
        current_data = self.controller.get_current_data()
        advice = self.controller.generate_health_advice(current_data)
        self.monitor_tab.display_health_advice(advice)

    def apply_alarm_settings(self, settings):
        """应用报警设置"""
        self.controller.update_alarm_settings(settings)

    def clear_data(self):
        """清空所有数据"""
        reply = QMessageBox.question(
            self,
            "确认",
            "确定要清空所有数据吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.controller.clear_data()
            self.monitor_tab.clear_data()

    def closeEvent(self, event):
        """窗口关闭事件"""
        # 确保断开串口连接
        self.disconnect_serial()
        event.accept()