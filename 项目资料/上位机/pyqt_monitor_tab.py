#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据监测标签页模块 - PyQt6版本
完全复制原Tkinter版本的界面和功能
"""

import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QGroupBox, QFrame, QSplitter, QMessageBox, QSizePolicy, QTextEdit
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QFont, QPalette, QColor

# 设置matplotlib后端
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties

# 导入实时图表窗口
from .pyqt_realtime_chart import RealtimeChartWindow


class MonitorTab(QWidget):
    """数据监测标签页 - PyQt6版本"""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.chart_enabled = False
        self.realtime_chart = RealtimeChartWindow(main_window)

        # 创建界面
        self.create_widgets()

        # 设置matplotlib中文字体
        self.setup_matplotlib_font()

    def setup_matplotlib_font(self):
        """设置matplotlib中文字体"""
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False

    def create_widgets(self):
        """创建界面组件"""
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 创建主要区域
        self.create_main_layout(main_layout)

        # 创建控制按钮区域
        self.create_control_buttons(main_layout)

        # 创建图表区域
        self.create_chart_area(main_layout)

        # 创建警报和健康建议区域
        self.create_alarm_advice_area(main_layout)

    def create_main_layout(self, layout):
        """创建主要布局"""
        # 顶部数据显示区域
        data_group = QGroupBox("实时生理指标")
        layout.addWidget(data_group)
        data_layout = QHBoxLayout(data_group)

        # 创建三列布局，等比例分布
        data_layout.setSpacing(20)

        # 体温显示
        self.create_metric_display(data_layout, "TEMP", "体温监测", "temp_display", "#FF6B6B")

        # 心率显示
        self.create_metric_display(data_layout, "BPM", "心率监测", "heart_display", "#4ECDC4")

        # 运动状态显示
        self.create_metric_display(data_layout, "STATUS", "运动状态", "movement_display", "#45B7D1")

    def create_metric_display(self, layout, icon, label, attr_name, color):
        """创建指标显示组件"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.Box)
        frame.setStyleSheet(f"""
            QFrame {{
                border: 1px solid #cccccc;
                border-radius: 5px;
                background-color: white;
            }}
        """)

        layout.addWidget(frame)
        v_layout = QVBoxLayout(frame)
        v_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 状态指示器
        indicator_frame = QFrame()
        indicator_frame.setFixedHeight(40)
        indicator_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 3px;
            }}
        """)
        v_layout.addWidget(indicator_frame)

        indicator_layout = QHBoxLayout(indicator_frame)
        indicator_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 图标标签
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Consolas", 14, QFont.Weight.Bold))
        icon_label.setStyleSheet("color: white;")
        indicator_layout.addWidget(icon_label)

        # 数值显示
        value_label = QLabel("--")
        value_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v_layout.addWidget(value_label)
        setattr(self, attr_name, value_label)

        # 标签
        label_widget = QLabel(label)
        label_widget.setFont(QFont("Microsoft YaHei", 10))
        label_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v_layout.addWidget(label_widget)

    def create_control_buttons(self, layout):
        """创建控制按钮区域"""
        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        layout.addWidget(control_frame)

        # 保存按钮
        save_btn = QPushButton("保存数据")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        save_btn.clicked.connect(self.main_window.save_data)
        control_layout.addWidget(save_btn)

        # 实时图表按钮
        chart_btn = QPushButton("实时图表")
        chart_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e68900;
            }
        """)
        chart_btn.clicked.connect(self.open_realtime_chart)
        control_layout.addWidget(chart_btn)

        # 健康建议按钮
        advice_btn = QPushButton("健康建议")
        advice_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        advice_btn.clicked.connect(self.main_window.generate_health_advice)
        control_layout.addWidget(advice_btn)

        control_layout.addStretch()

    def create_chart_area(self, layout):
        """创建图表区域"""
        self.chart_group = QGroupBox("实时数据曲线")
        layout.addWidget(self.chart_group)
        chart_layout = QVBoxLayout(self.chart_group)

        # 创建图表组件
        self.create_chart_widgets(chart_layout)

        # 初始隐藏图表
        self.chart_group.hide()

    def create_chart_widgets(self, layout):
        """创建图表组件"""
        # 创建图表
        self.figure = Figure(figsize=(12, 3), dpi=80)
        self.figure.patch.set_facecolor('#f8f9fa')

        # 创建子图
        self.temp_axis = self.figure.add_subplot(131)
        self.heart_axis = self.figure.add_subplot(132)
        self.accel_axis = self.figure.add_subplot(133)

        # 设置子图标题
        self.temp_axis.set_title("体温", fontsize=12, pad=10)
        self.heart_axis.set_title("心率", fontsize=12, pad=10)
        self.accel_axis.set_title("加速度", fontsize=12, pad=10)

        # 设置坐标轴标签
        self.temp_axis.set_ylabel("温度(°C)", fontsize=10)
        self.heart_axis.set_ylabel("心率(bpm)", fontsize=10)
        self.accel_axis.set_ylabel("加速度(g)", fontsize=10)

        # 设置网格
        for axis in [self.temp_axis, self.heart_axis, self.accel_axis]:
            axis.grid(True, linestyle='--', alpha=0.7)
            axis.set_facecolor('#ffffff')

        # 调整布局
        self.figure.tight_layout()

        # 创建画布
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

    def create_alarm_advice_area(self, layout):
        """创建警报和健康建议区域"""
        # 创建水平分割的区域
        alarm_frame = QFrame()
        alarm_layout = QHBoxLayout(alarm_frame)
        layout.addWidget(alarm_frame)

        # 警报信息区域
        alarm_group = QGroupBox("系统警报")
        alarm_layout.addWidget(alarm_group)
        alarm_v_layout = QVBoxLayout(alarm_group)

        self.alarm_text = QTextEdit()
        self.alarm_text.setFont(QFont("Microsoft YaHei", 10))
        self.alarm_text.setReadOnly(True)
        self.alarm_text.setMaximumHeight(200)
        alarm_v_layout.addWidget(self.alarm_text)

        # 健康建议区域
        advice_group = QGroupBox("健康建议")
        alarm_layout.addWidget(advice_group)
        advice_v_layout = QVBoxLayout(advice_group)

        self.advice_text = QTextEdit()
        self.advice_text.setFont(QFont("Microsoft YaHei", 10))
        self.advice_text.setReadOnly(True)
        self.advice_text.setMaximumHeight(200)
        advice_v_layout.addWidget(self.advice_text)

    # 数据更新方法
    def update_display(self, data):
        """更新数据显示"""
        # 更新体温显示
        temp = data.get('temperature', 0)
        self.temp_display.setText(f"{temp:.1f}°C")

        # 更新心率显示
        heart = data.get('heart_rate', 0)
        self.heart_display.setText(f"{heart} BPM")

        # 更新运动状态
        accel_x = data.get('accel_x', 0)
        accel_y = data.get('accel_y', 0)
        accel_z = data.get('accel_z', 0)
        total_accel = (accel_x**2 + accel_y**2 + accel_z**2)**0.5

        if total_accel < 0.5:
            status = "静止"
        elif total_accel < 1.5:
            status = "慢走"
        else:
            status = "运动"

        self.movement_display.setText(status)

        # 更新图表
        self.update_chart()

    def update_chart(self):
        """更新图表"""
        if not self.chart_enabled:
            return

        # 这里可以添加图表更新逻辑
        # 由于原版也没有具体的图表更新代码，这里保持简单
        pass

    def add_alarm_message(self, message):
        """添加警报消息"""
        self.alarm_text.append(message)
        # 滚动到底部
        scrollbar = self.alarm_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def display_health_advice(self, advice_list):
        """显示健康建议"""
        self.advice_text.clear()
        for i, advice in enumerate(advice_list, 1):
            self.advice_text.append(f"{i}. {advice}")
        # 滚动到底部
        scrollbar = self.advice_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def open_realtime_chart(self):
        """打开实时图表窗口"""
        # 注册控制器的回调到图表窗口
        if hasattr(self.main_window, 'controller'):
            # 传递当前数据
            current_data = self.main_window.controller.get_current_data()
            self.realtime_chart.update_data(current_data)

            # 注册回调
            self.main_window.controller.register_callback('data_received', self.realtime_chart.update_data)

        self.realtime_chart.show()
        self.realtime_chart.raise_()
        self.realtime_chart.activateWindow()

    def clear_data(self):
        """清空所有显示数据"""
        self.temp_display.setText("--")
        self.heart_display.setText("--")
        self.movement_display.setText("--")

        # 清空警报和建议
        self.alarm_text.clear()
        self.advice_text.clear()

    def toggle_chart(self, enabled):
        """切换图表显示"""
        self.chart_enabled = enabled
        if enabled:
            self.chart_group.show()
        else:
            self.chart_group.hide()