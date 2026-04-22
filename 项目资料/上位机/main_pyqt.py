#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
健康监测系统 - PyQt6版本主程序入口
"""

import sys
import os
import traceback
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    # PyQt6版本的GUI
    from pyqt_main_window import HealthMonitorApp

    def main():
        """主函数"""
        print("=" * 60)
        print("健康监测系统 - PyQt6版本")
        print("=" * 60)
        print("正在启动应用...")

        try:
            # 创建QApplication实例
            app = QApplication(sys.argv)

            # 设置应用程序属性
            app.setApplicationName("健康监测系统")
            app.setApplicationVersion("2.0")
            app.setStyle('Fusion')

            # 设置全局字体
            font = QFont("Microsoft YaHei", 9)
            app.setFont(font)

            # 创建并运行主窗口
            window = HealthMonitorApp()
            print("应用启动成功！")
            window.show()

            # 运行应用程序事件循环
            sys.exit(app.exec())

        except KeyboardInterrupt:
            print("\n程序被用户中断")
        except Exception as e:
            print(f"程序运行错误: {e}")
            print("\n详细错误信息:")
            traceback.print_exc()
        finally:
            print("程序已退出")

    if __name__ == "__main__":
        main()

except ImportError as e:
    print(f"导入模块失败: {e}")
    print("\n请检查以下问题：")
    print("1. 是否已安装所有必需的依赖库？")
    print("2. 项目结构是否正确？")
    print("3. Python版本是否兼容？")
    print("\n尝试运行: pip install pyqt6 pyqtgraph pyserial matplotlib")
    sys.exit(1)