#!/usr/bin/env python3
"""
基本用法示例
展示最简单的授权流程
"""

# 安装: pip install git+https://github.com/gongwenqing314/AuTool.git git+https://github.com/gongwenqing314/auauth.git
from auauth import authorize_device


def main():
    print("=" * 60)
    print("AuAuth 基本用法示例")
    print("=" * 60)
    
    # 配置
    gateway_ip = "192.168.10.1"
    license_file = "license.lic"  # 请替换为实际路径
    
    print(f"\n网关IP: {gateway_ip}")
    print(f"许可证: {license_file}")
    print("\n开始授权...")
    
    try:
        # 一行代码完成授权
        result = authorize_device(
            gateway_ip=gateway_ip,
            license_file=license_file
        )
        
        if result.success:
            print("\n✓ 授权成功!")
            print(f"  用户名: {result.access_user}")
            print(f"  密码: {result.access_password}")
            print(f"  Telnet地址: {result.telnet_address}")
            print(f"  Telnet端口: {result.telnet_port}")
            
            # 获取凭证字典
            creds = result.get_telnet_credentials()
            print(f"\n  凭证字典: {creds}")
        else:
            print(f"\n✗ 授权失败: {result.message}")
            
    except Exception as e:
        print(f"\n✗ 错误: {e}")


if __name__ == "__main__":
    main()
