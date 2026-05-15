#!/usr/bin/env python3
"""
高级用法示例
展示异常处理、高级配置和客户端复用
"""

from auauth import AuthClient, AuthConfig, authorize_device
from auauth.exceptions import (
    AuAuthError,
    LicenseError,
    AuthFlowError,
    NetworkError,
    CryptoError,
    ConfigError,
)


def example_1_basic_with_exception_handling():
    """示例1：带异常处理的基本用法"""
    print("\n" + "=" * 60)
    print("示例1：带异常处理的基本用法")
    print("=" * 60)
    
    try:
        result = authorize_device(
            gateway_ip="192.168.10.1",
            license_file="license.lic"
        )
        
        if result.success:
            print("✓ 授权成功!")
            print(f"  用户名: {result.access_user}")
        else:
            print(f"✗ 授权失败: {result.message}")
            
    except LicenseError as e:
        print(f"✗ 许可证错误: {e}")
        print(f"  许可证路径: {e.license_path}")
        
    except AuthFlowError as e:
        print(f"✗ 授权流程错误")
        print(f"  步骤: {e.step}")
        print(f"  消息: {e.message}")
        print(f"  错误码: {e.code}")
        
    except NetworkError as e:
        print(f"✗ 网络错误: {e}")
        if e.status_code:
            print(f"  HTTP状态码: {e.status_code}")
            
    except CryptoError as e:
        print(f"✗ 加密错误: {e}")
        
    except ConfigError as e:
        print(f"✗ 配置错误: {e}")
        
    except AuAuthError as e:
        print(f"✗ 授权错误: {e}")


def example_2_advanced_client():
    """示例2：使用高级客户端"""
    print("\n" + "=" * 60)
    print("示例2：使用高级客户端")
    print("=" * 60)
    
    try:
        # 创建详细配置
        config = AuthConfig(
            gateway_ip="192.168.10.1",
            license_path="license.lic",
            admin_account="CMCCAdmin",
            admin_password="aDm8H%MdA",
            gateway_port=23,
            timeout=5,
            debug=False
        )
        
        print("配置信息:")
        print(f"  网关: {config.gateway_ip}:{config.gateway_port}")
        print(f"  账号: {config.admin_account}")
        print(f"  超时: {config.timeout}秒")
        
        # 创建客户端
        client = AuthClient(config)
        
        # 执行授权
        result = client.authorize()
        
        if result.success:
            print("\n✓ 授权成功!")
            creds = result.get_telnet_credentials()
            print(f"\nTelnet连接信息:")
            print(f"  主机: {creds['host']}")
            print(f"  端口: {creds['port']}")
            print(f"  用户名: {creds['username']}")
            print(f"  密码: {creds['password']}")
        else:
            print(f"\n✗ 授权失败: {result.message}")
            
    except Exception as e:
        print(f"\n✗ 错误: {e}")


def example_3_invalid_config():
    """示例3：无效配置的错误处理"""
    print("\n" + "=" * 60)
    print("示例3：无效配置的错误处理")
    print("=" * 60)
    
    # 测试空IP
    try:
        config = AuthConfig(
            gateway_ip="",
            license_path="license.lic"
        )
    except ConfigError as e:
        print(f"✓ 捕获配置错误（空IP）: {e}")
    
    # 测试不存在的许可证
    try:
        config = AuthConfig(
            gateway_ip="192.168.10.1",
            license_path="/nonexistent/license.lic"
        )
    except LicenseError as e:
        print(f"✓ 捕获许可证错误（文件不存在）: {e}")


def example_4_complete_workflow():
    """示例4：完整工作流程"""
    print("\n" + "=" * 60)
    print("示例4：完整工作流程")
    print("=" * 60)
    
    print("\n步骤1: 准备配置")
    print("-" * 40)
    
    try:
        config = AuthConfig(
            gateway_ip="192.168.10.1",
            license_path="license.lic",
            debug=True
        )
        print("✓ 配置创建成功")
        
        print("\n步骤2: 创建客户端")
        print("-" * 40)
        client = AuthClient(config)
        print("✓ 客户端创建成功")
        
        print("\n步骤3: 执行授权")
        print("-" * 40)
        result = client.authorize()
        
        print("\n步骤4: 处理结果")
        print("-" * 40)
        if result.success:
            print("✓ 授权成功!")
            print(f"\n结果详情:")
            print(f"  成功标志: {result.success}")
            print(f"  消息: {result.message}")
            print(f"  访问用户: {result.access_user}")
            print(f"  访问密码: {'*' * len(result.access_password)}")
            print(f"  Telnet地址: {result.telnet_address}")
            print(f"  Telnet端口: {result.telnet_port}")
            
            # 获取凭证
            creds = result.get_telnet_credentials()
            print(f"\n  凭证字典:")
            for key, value in creds.items():
                if key == "password":
                    value = "*" * len(value)
                print(f"    {key}: {value}")
        else:
            print(f"✗ 授权失败: {result.message}")
            
    except Exception as e:
        print(f"\n✗ 流程异常: {e}")


def main():
    print("=" * 60)
    print("AuAuth 高级用法示例")
    print("=" * 60)
    
    # 运行示例
    example_1_basic_with_exception_handling()
    example_2_advanced_client()
    example_3_invalid_config()
    example_4_complete_workflow()
    
    print("\n" + "=" * 60)
    print("示例运行完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
