#!/usr/bin/env python3
"""
Telnet集成示例
展示如何使用授权结果连接Telnet
"""

import telnetlib
import time
from auauth import authorize_device


def get_auth_credentials(gateway_ip: str, license_file: str):
    """
    获取授权凭证
    
    Args:
        gateway_ip: 网关IP
        license_file: 许可证文件路径
        
    Returns:
        dict: 包含host, port, username, password的字典
        
    Raises:
        Exception: 授权失败
    """
    result = authorize_device(
        gateway_ip=gateway_ip,
        license_file=license_file
    )
    
    if not result.success:
        raise Exception(f"授权失败: {result.message}")
    
    return result.get_telnet_credentials()


def connect_telnet(credentials: dict, timeout: int = 10):
    """
    使用凭证连接Telnet
    
    Args:
        credentials: 包含host, port, username, password的字典
        timeout: 连接超时秒数
        
    Returns:
        telnetlib.Telnet: 已连接的Telnet对象
    """
    host = credentials["host"]
    port = credentials["port"]
    username = credentials["username"]
    password = credentials["password"]
    
    print(f"\n连接Telnet: {host}:{port}")
    
    # 创建Telnet连接
    tn = telnetlib.Telnet(host, port, timeout=timeout)
    
    # 等待登录提示
    print("等待登录提示...")
    tn.read_until(b"login: ", timeout=5)
    
    # 发送用户名
    print(f"发送用户名: {username}")
    tn.write(username.encode() + b"\n")
    
    # 等待密码提示
    print("等待密码提示...")
    tn.read_until(b"Password: ", timeout=5)
    
    # 发送密码
    print("发送密码...")
    tn.write(password.encode() + b"\n")
    
    # 等待命令提示符
    print("等待命令提示符...")
    time.sleep(1)
    
    # 读取欢迎信息
    output = tn.read_very_eager().decode('utf-8', errors='ignore')
    print(f"\n登录成功!\n")
    print("-" * 40)
    print(output)
    print("-" * 40)
    
    return tn


def execute_commands(tn: telnetlib.Telnet, commands: list):
    """
    在Telnet会话中执行命令
    
    Args:
        tn: Telnet连接对象
        commands: 要执行的命令列表
    """
    for cmd in commands:
        print(f"\n执行命令: {cmd}")
        tn.write(cmd.encode() + b"\n")
        time.sleep(1)
        
        output = tn.read_very_eager().decode('utf-8', errors='ignore')
        print(output)


def main():
    print("=" * 60)
    print("Telnet集成示例")
    print("=" * 60)
    
    # 配置
    gateway_ip = "192.168.10.1"
    license_file = "license.lic"
    
    try:
        # 步骤1: 获取授权凭证
        print("\n步骤1: 获取授权凭证")
        print("-" * 40)
        creds = get_auth_credentials(gateway_ip, license_file)
        print(f"✓ 授权成功")
        print(f"  用户名: {creds['username']}")
        print(f"  密码: {'*' * len(creds['password'])}")
        
        # 步骤2: 连接Telnet
        print("\n步骤2: 连接Telnet")
        print("-" * 40)
        tn = connect_telnet(creds)
        
        # 步骤3: 执行命令
        print("\n步骤3: 执行命令")
        print("-" * 40)
        commands = [
            "show version",
            "show running-config",
            "exit"
        ]
        execute_commands(tn, commands)
        
        # 关闭连接
        tn.close()
        print("\n✓ Telnet连接已关闭")
        
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
