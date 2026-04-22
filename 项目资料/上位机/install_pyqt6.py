#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyQt6 安装脚本
"""

import subprocess
import sys

def install_package(package_name):
    """安装Python包"""
    try:
        print(f"正在安装 {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"✅ {package_name} 安装成功！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {package_name} 安装失败: {e}")
        return False

def install_with_options(package_name, options=None):
    """使用选项安装Python包"""
    try:
        cmd = [sys.executable, "-m", "pip", "install", package_name]
        if options:
            cmd.extend(options)

        print(f"正在使用选项安装 {package_name}...")
        print(f"命令: {' '.join(cmd)}")
        subprocess.check_call(cmd)
        print(f"✅ {package_name} 安装成功！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {package_name} 安装失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("PyQt6 健康监测系统 - 依赖安装脚本")
    print("=" * 60)

    # 需要安装的包列表
    packages = [
        "PyQt6",
        "matplotlib",
        "numpy"
    ]

    # 安装选项
    install_options = [
        "--trusted-host", "pypi.org",
        "--trusted-host", "pypi.python.org",
        "--trusted-host", "files.pythonhosted.org",
        "--timeout", "1000"
    ]

    print("开始安装依赖包...")
    print("如果出现SSL错误，脚本将使用信任主机选项重试")
    print()

    success_count = 0

    for package in packages:
        print(f"\n{'='*40}")
        print(f"安装 {package}")
        print(f"{'='*40}")

        # 首先尝试正常安装
        if install_package(package):
            success_count += 1
        else:
            print("尝试使用信任主机选项...")
            # 如果失败，使用信任主机选项
            if install_with_options(package, install_options):
                success_count += 1
            else:
                # 尝试使用不同的索引
                print("尝试使用清华大学镜像...")
                tsinghua_options = [
                    "-i", "https://pypi.tuna.tsinghua.edu.cn/simple/",
                    "--trusted-host", "pypi.tuna.tsinghua.edu.cn"
                ]
                if install_with_options(package, tsinghua_options):
                    success_count += 1

    print(f"\n{'='*60}")
    print("安装完成！")
    print(f"成功安装: {success_count}/{len(packages)} 个包")

    if success_count == len(packages):
        print("🎉 所有依赖包安装成功！")
        print("现在可以运行: python main_pyqt.py")
    else:
        print("⚠️  部分包安装失败，请手动安装缺失的包")
        print("或者使用原版本: python main.py")

    print(f"{'='*60}")

if __name__ == "__main__":
    main()