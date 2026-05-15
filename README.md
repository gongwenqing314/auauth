# AuAuth - 设备授权库

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

AuAuth 是一个用于网关设备授权认证的 Python 库，支持 SM2/SM3 国密算法、许可证验证和 Telnet 授权流程。

## 特性

- 🔐 **国密算法支持**：SM2 加密/签名、SM3 哈希、SM4/AES 对称加密
- 📜 **许可证验证**：支持 `.lic` 许可证文件解析和验证
- 🔌 **Telnet 授权**：完整的 7 步网关授权流程
- 🎯 **简单易用**：一行代码完成授权
- 🛡️ **类型安全**：完整的类型注解支持
- 📦 **零配置**：开箱即用，合理的默认值

## 安装

### 前提条件

本库依赖 [AuTool](https://github.com/gongwenqing314/AuTool) 核心模块，需要先安装。

### 安装步骤

```bash
# 步骤1: 安装 AuTool 核心模块（私有仓库需要认证）
pip install git+https://github.com/gongwenqing314/AuTool.git

# 步骤2: 安装 AuAuth
pip install git+https://github.com/gongwenqing314/auauth.git
```

### 一行命令安装（推荐）

```bash
pip install git+https://github.com/gongwenqing314/AuTool.git git+https://github.com/gongwenqing314/auauth.git
```

### 开发模式安装

```bash
# 克隆仓库
git clone https://github.com/gongwenqing314/auauth.git
git clone https://github.com/gongwenqing314/AuTool.git

# 开发模式安装
cd AuTool && pip install -e .
cd ../auauth && pip install -e .
```

### 私有仓库访问

由于 AuTool 是私有仓库，安装时需要 GitHub 认证：

**方式1：使用 Personal Access Token**
```bash
# 生成Token: GitHub → Settings → Developer settings → Personal access tokens
pip install git+https://<TOKEN>@github.com/gongwenqing314/AuTool.git
```

**方式2：使用 SSH**
```bash
# 配置SSH密钥后
pip install git+ssh://git@github.com/gongwenqing314/AuTool.git
```

## 快速开始

### 基本用法

```python
from auauth import authorize_device

# 一行代码完成授权
result = authorize_device(
    gateway_ip="192.168.10.1",
    license_file="/path/to/license.lic"
)

if result.success:
    print(f"授权成功!")
    print(f"用户名: {result.access_user}")
    print(f"密码: {result.access_password}")
    print(f"Telnet: {result.telnet_address}:{result.telnet_port}")
    
    # 获取 Telnet 连接凭证
    creds = result.get_telnet_credentials()
else:
    print(f"授权失败: {result.message}")
```

### 完整参数

```python
from auauth import authorize_device

result = authorize_device(
    gateway_ip="192.168.10.1",           # 网关IP（必需）
    license_file="/path/to/license.lic",  # 许可证文件路径（必需）
    admin_account="CMCCAdmin",            # 管理员账号（默认）
    admin_password="aDm8H%MdA",           # 管理员密码（默认）
    gateway_port=23,                       # Telnet端口（默认23）
    public_key_file=None,                  # 公钥文件路径（默认使用内置）
    timeout=5,                             # HTTP超时秒数（默认5）
    debug=False                            # 调试模式（默认关闭）
)
```

### 高级用法

```python
from auauth import AuthClient, AuthConfig
from auauth.exceptions import LicenseError, AuthFlowError, NetworkError

# 创建配置
config = AuthConfig(
    gateway_ip="192.168.10.1",
    license_path="/path/to/license.lic",
    admin_account="CMCCAdmin",
    admin_password="aDm8H%MdA",
    gateway_port=23,
    timeout=5,
    debug=False
)

# 创建客户端
try:
    client = AuthClient(config)
    result = client.authorize()
    
    if result.success:
        print("授权成功!")
        # 使用结果...
        
except LicenseError as e:
    print(f"许可证错误: {e}")
    print(f"许可证路径: {e.license_path}")
    
except AuthFlowError as e:
    print(f"授权流程错误（步骤{e.step}）: {e.message}")
    if e.code:
        print(f"错误码: {e.code}")
        
except NetworkError as e:
    print(f"网络错误: {e}")
    
except Exception as e:
    print(f"未知错误: {e}")
```

## 异常处理

```python
from auauth import authorize_device
from auauth.exceptions import (
    AuAuthError,        # 基础异常，捕获所有
    LicenseError,       # 许可证相关
    AuthFlowError,      # 授权流程错误
    NetworkError,       # 网络错误
    CryptoError,        # 加密错误
    ConfigError,        # 配置错误
)

try:
    result = authorize_device(
        gateway_ip="192.168.10.1",
        license_file="license.lic"
    )
except LicenseError as e:
    # 许可证文件不存在、格式错误、已过期等
    print(f"许可证问题: {e}")
except AuthFlowError as e:
    # 授权流程某步骤失败
    print(f"步骤{e.step}失败: {e.message}")
except NetworkError as e:
    # 连接超时、连接被拒绝等
    print(f"网络问题: {e}")
except AuAuthError as e:
    # 捕获所有其他 AuAuth 异常
    print(f"授权错误: {e}")
```

## 集成示例

### Telnet 连接（使用授权结果）

```python
import telnetlib
import time
from auauth import authorize_device

# 授权
def get_auth_credentials(gateway_ip: str, license_file: str):
    result = authorize_device(
        gateway_ip=gateway_ip,
        license_file=license_file
    )
    
    if not result.success:
        raise Exception(f"授权失败: {result.message}")
    
    return result.get_telnet_credentials()

# 连接 Telnet
def connect_telnet(credentials: dict):
    tn = telnetlib.Telnet(
        host=credentials["host"],
        port=credentials["port"],
        timeout=10
    )
    
    # 等待登录提示
    tn.read_until(b"login: ", timeout=5)
    tn.write(credentials["username"].encode() + b"\n")
    
    # 等待密码提示
    tn.read_until(b"Password: ", timeout=5)
    tn.write(credentials["password"].encode() + b"\n")
    
    # 等待命令提示符
    time.sleep(1)
    output = tn.read_very_eager().decode()
    print(output)
    
    return tn

# 主流程
if __name__ == "__main__":
    creds = get_auth_credentials("192.168.10.1", "license.lic")
    tn = connect_telnet(creds)
    # 执行命令...
    tn.close()
```

## 项目结构

```
auauth/
├── src/
│   └── auauth/              # 库源码
│       ├── __init__.py      # 公开API
│       ├── api.py           # 主要接口实现
│       └── exceptions.py    # 异常定义
├── tests/                   # 测试用例
├── docs/                    # 文档
├── examples/                # 使用示例
├── pyproject.toml           # 打包配置
└── README.md                # 本文件
```

## 相关仓库

| 仓库 | 说明 |
|------|------|
| [AuTool](https://github.com/gongwenqing314/AuTool) | 核心模块（SM2加密、许可证验证、授权流程） |
| [auauth](https://github.com/gongwenqing314/auauth) | 包装库（简化API、异常处理） |

## 依赖

- Python >= 3.8
- gmssl >= 3.2.2 (SM2/SM3 国密算法)
- pycryptodome >= 3.15.0 (AES 加密)
- requests >= 2.28.0 (HTTP 请求)
- psutil >= 5.9.0 (硬件信息获取)

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 支持

如有问题，请提交 [GitHub Issue](https://github.com/gongwenqing314/auauth/issues)
