#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时图表窗口 - PyQt6版本
完全复制原Tkinter版本的界面和功能
"""

import numpy as np
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QGroupBox, QLabel, QGridLayout, QCheckBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QFont

# 设置matplotlib后端
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from collections import deque


class RealtimeChartWindow(QMainWindow):
    """实时图表窗口 - PyQt6版本"""

    def __init__(self, main_window):
        super().__init__()

        self.main_window = main_window

        # 数据缓存
        self.max_points = 100
        self.time_data = deque(maxlen=self.max_points)
        self.temp_data = deque(maxlen=self.max_points)
        self.heart_data = deque(maxlen=self.max_points)
        self.accel_data = deque(maxlen=self.max_points)

        # 设置窗口
        self.setWindowTitle("实时数据图表")
        self.setGeometry(200, 200, 1000, 600)

        # 创建界面
        self.setup_ui()

        # 设置matplotlib中文字体
        self.setup_matplotlib_font()

        # 初始化数据
        self.init_data()

    def setup_matplotlib_font(self):
        """设置matplotlib中文字体"""
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False

    def setup_ui(self):
        """创建界面"""
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 创建主布局
        main_layout = QVBoxLayout(central_widget)

        # 创建控制区域
        self.create_control_area(main_layout)

        # 创建图表区域
        self.create_chart_area(main_layout)

    def create_control_area(self, layout):
        """创建控制区域"""
        control_group = QGroupBox("图表控制")
        layout.addWidget(control_group)
        control_layout = QHBoxLayout(control_group)

        # 图表选择复选框
        self.show_temp_check = QCheckBox("体温")
        self.show_temp_check.setChecked(True)
        self.show_temp_check.toggled.connect(self.update_chart_display)
        control_layout.addWidget(self.show_temp_check)

        self.show_heart_check = QCheckBox("心率")
        self.show_heart_check.setChecked(True)
        self.show_heart_check.toggled.connect(self.update_chart_display)
        control_layout.addWidget(self.show_heart_check)

        self.show_accel_check = QCheckBox("加速度")
        self.show_accel_check.setChecked(True)
        self.show_accel_check.toggled.connect(self.update_chart_display)
        control_layout.addWidget(self.show_accel_check)

        control_layout.addStretch()

        # 清空数据按钮
        clear_btn = QPushButton("清空数据")
        clear_btn.clicked.connect(self.clear_data)
        control_layout.addWidget(clear_btn)

    def create_chart_area(self, layout):
        """创建图表区域"""
        chart_group = QGroupBox("实时曲线")
        layout.addWidget(chart_group)
        chart_layout = QVBoxLayout(chart_group)

        # 创建matplotlib图表
        self.figure = Figure(figsize=(12, 6), dpi=80)
        self.figure.patch.set_facecolor('#f8f9fa')

        # 创建子图
        self.temp_axis = self.figure.add_subplot(311)
        self.heart_axis = self.figure.add_subplot(312)
        self.accel_axis = self.figure.add_subplot(313)

        # 设置子图标题和标签
        self.temp_axis.set_title("体温变化", fontsize=12, pad=10)
        self.temp_axis.set_ylabel("温度(°C)", fontsize=10)
        self.temp_axis.grid(True, linestyle='--', alpha=0.7)

        self.heart_axis.set_title("心率变化", fontsize=12, pad=10)
        self.heart_axis.set_ylabel("心率(bpm)", fontsize=10)
        self.heart_axis.grid(True, linestyle='--', alpha=0.7)

        self.accel_axis.set_title("加速度变化", fontsize=12, pad=10)
        self.accel_axis.set_ylabel("加速度(g)", fontsize=10)
        self.accel_axis.set_xlabel("时间点", fontsize=10)
        self.accel_axis.grid(True, linestyle='--', alpha=0.7)

        # 调整布局
        self.figure.tight_layout()

        # 创建画布
        self.canvas = FigureCanvas(self.figure)
        chart_layout.addWidget(self.canvas)

    def init_data(self):
        """初始化数据"""
        # 初始化空的数据
        for i in range(self.max_points):
            self.time_data.append(i)
            self.temp_data.append(36.5)
            self.heart_data.append(75)
            self.accel_data.append(0.0)

        # 初始化图表
        self.update_chart_display()

    @pyqtSlot(dict)
    def update_data(self, data):
        """更新数据"""
        # 添加新数据点
        self.time_data.append(len(self.time_data))
        self.temp_data.append(data.get('temperature', 36.5))
        self.heart_data.append(data.get('heart_rate', 75))

        # 计算总加速度
        accel_x = data.get('accel_x', 0)
        accel_y = data.get('accel_y', 0)
        accel_z = data.get('accel_z', 0)
        total_accel = (accel_x**2 + accel_y**2 + accel_z**2)**0.5
        self.accel_data.append(total_accel)

        # 更新图表
        self.update_chart_display()

    def update_chart_display(self):
        """更新图表显示"""
        # 清除所有子图
        self.temp_axis.clear()
        self.heart_axis.clear()
        self.accel_axis.clear()

        # 重新设置网格
        self.temp_axis.grid(True, linestyle='--', alpha=0.7)
        self.heart_axis.grid(True, linestyle='--', alpha=0.7)
        self.accel_axis.grid(True, linestyle='--', alpha=0.7)

        # 绘制数据
        time_array = np.array(list(self.time_data))

        if self.show_temp_check.isChecked() and len(self.temp_data) > 0:
            temp_array = np.array(list(self.temp_data))
            self.temp_axis.plot(time_array, temp_array, 'r-', linewidth=2, label='体温')
            self.temp_axis.set_title("体温变化", fontsize=12, pad=10)
            self.temp_axis.set_ylabel("温度(°C)", fontsize=10)
            self.temp_axis.set_ylim([35, 40])

        if self.show_heart_check.isChecked() and len(self.heart_data) > 0:
            heart_array = np.array(list(self.heart_data))
            self.heart_axis.plot(time_array, heart_array, 'b-', linewidth=2, label='心率')
            self.heart_axis.set_title("心率变化", fontsize=12, pad=10)
            self.heart_axis.set_ylabel("心率(bpm)", fontsize=10)
            self.heart_axis.set_ylim([40, 180])

        if self.show_accel_check.isChecked() and len(self.accel_data) > 0:
            accel_array = np.array(list(self.accel_data))
            self.accel_axis.plot(time_array, accel_array, 'g-', linewidth=2, label='加速度')
            self.accel_axis.set_title("加速度变化", fontsize=12, pad=10)
            self.accel_axis.set_ylabel("加速度(g)", fontsize=10)
            self.accel_axis.set_xlabel("时间点", fontsize=10)
            self.accel_axis.set_ylim([0, 5])

        # 调整布局
        self.figure.tight_layout()

        # 刷新画布
        self.canvas.draw()

    def clear_data(self):
        """清空数据"""
        self.time_data.clear()
        self.temp_data.clear()
        self.heart_data.clear()
        self.accel_data.clear()

        # 重新初始化
        self.init_data()