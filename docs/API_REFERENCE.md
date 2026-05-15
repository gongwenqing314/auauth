# AuAuth API 参考文档

> 安装: `pip install git+https://github.com/gongwenqing314/AuTool.git git+https://github.com/gongwenqing314/auauth.git`

## 核心函数

### `authorize_device()`

一行代码完成设备授权。

```python
from auauth import authorize_device

result = authorize_device(
    gateway_ip: str,
    license_file: str,
    admin_account: str = "CMCCAdmin",
    admin_password: str = "aDm8H%MdA",
    gateway_port: int = 23,
    public_key_file: Optional[str] = None,
    timeout: int = 5,
    debug: bool = False
) -> AuthResult
```

**参数：**

| 参数名 | 类型 | 必需 | 默认值 | 说明 |
|--------|------|------|--------|------|
| gateway_ip | str | ✓ | - | 网关IP地址 |
| license_file | str | ✓ | - | 许可证文件路径 |
| admin_account | str | ✗ | "CMCCAdmin" | 管理员账号 |
| admin_password | str | ✗ | "aDm8H%MdA" | 管理员密码 |
| gateway_port | int | ✗ | 23 | Telnet端口 |
| public_key_file | str | ✗ | None | 公钥文件路径 |
| timeout | int | ✗ | 5 | HTTP超时秒数 |
| debug | bool | ✗ | False | 调试模式 |

**返回值：**

`AuthResult` - 授权结果对象

**异常：**

- `LicenseError` - 许可证验证失败
- `AuthFlowError` - 授权流程失败
- `NetworkError` - 网络连接错误
- `CryptoError` - 加密/解密错误

**示例：**

```python
from auauth import authorize_device

result = authorize_device(
    gateway_ip="192.168.10.1",
    license_file="license.lic"
)

if result.success:
    print(f"授权成功: {result.access_user}")
else:
    print(f"授权失败: {result.message}")
```

---

## 核心类

### `AuthConfig`

授权配置类。

```python
from auauth import AuthConfig

config = AuthConfig(
    gateway_ip: str,
    license_path: str,
    admin_account: str = "CMCCAdmin",
    admin_password: str = "aDm8H%MdA",
    gateway_port: int = 23,
    public_key_path: Optional[str] = None,
    timeout: int = 5,
    debug: bool = False
)
```

**属性：**

| 属性名 | 类型 | 说明 |
|--------|------|------|
| gateway_ip | str | 网关IP地址 |
| license_path | str | 许可证文件路径 |
| admin_account | str | 管理员账号 |
| admin_password | str | 管理员密码 |
| gateway_port | int | Telnet端口 |
| public_key_path | Optional[str] | 公钥文件路径 |
| timeout | int | HTTP超时秒数 |
| debug | bool | 调试模式 |

**异常：**

- `ConfigError` - 配置无效（空IP、许可证不存在等）

---

### `AuthClient`

授权客户端类。

```python
from auauth import AuthClient, AuthConfig

config = AuthConfig(...)
client = AuthClient(config)
result = client.authorize()
```

**方法：**

#### `authorize()` -> AuthResult

执行授权流程。

**返回值：**

`AuthResult` - 授权结果

**异常：**

- `LicenseError` - 许可证验证失败
- `AuthFlowError` - 授权流程失败
- `NetworkError` - 网络连接错误
- `CryptoError` - 加密/解密错误
- `AuAuthError` - autool_auth模块不可用

---

### `AuthResult`

授权结果类。

```python
from auauth import AuthResult

result = AuthResult(
    success: bool,
    message: str = "",
    access_user: str = "",
    access_password: str = "",
    telnet_address: str = "",
    telnet_port: int = 23,
    raw_result: Any = None
)
```

**属性：**

| 属性名 | 类型 | 说明 |
|--------|------|------|
| success | bool | 授权是否成功 |
| message | str | 结果消息 |
| access_user | str | 访问用户名（成功时） |
| access_password | str | 访问密码（成功时） |
| telnet_address | str | Telnet地址（成功时） |
| telnet_port | int | Telnet端口（成功时） |
| raw_result | Any | 内部原始结果 |

**方法：**

#### `get_telnet_credentials() -> Optional[Dict[str, str]]`

获取Telnet连接凭证。

**返回值：**

字典包含以下键值，授权失败时返回None：
- `host`: 主机地址
- `port`: 端口
- `username`: 用户名
- `password`: 密码

**示例：**

```python
creds = result.get_telnet_credentials()
if creds:
    print(f"连接: {creds['host']}:{creds['port']}")
    print(f"账号: {creds['username']}/{creds['password']}")
```

---

## 异常类

### 异常继承关系

```
AuAuthError (基类)
├── LicenseError
├── AuthFlowError
├── NetworkError
├── CryptoError
└── ConfigError
```

### `AuAuthError`

基础异常类。捕获此异常可捕获所有AuAuth相关异常。

### `LicenseError`

许可证相关错误。

**属性：**
- `license_path`: 许可证文件路径

### `AuthFlowError`

授权流程错误。

**属性：**
- `step`: 失败的步骤编号（2, 4, 6）
- `code`: 网关返回的错误码
- `message`: 错误描述

### `NetworkError`

网络连接错误。

**属性：**
- `url`: 请求的URL
- `status_code`: HTTP状态码

### `CryptoError`

加密/解密错误。

### `ConfigError`

配置错误。

---

## 使用模式

### 模式1：简单用法

```python
from auauth import authorize_device

result = authorize_device(
    gateway_ip="192.168.10.1",
    license_file="license.lic"
)

if result.success:
    creds = result.get_telnet_credentials()
    # 使用creds连接Telnet
```

### 模式2：带异常处理

```python
from auauth import authorize_device
from auauth.exceptions import LicenseError, AuthFlowError, NetworkError

try:
    result = authorize_device(...)
    if result.success:
        # 处理成功
        pass
    else:
        # 处理失败
        pass
except LicenseError as e:
    # 许可证问题
    pass
except AuthFlowError as e:
    # 授权流程问题
    print(f"步骤{e.step}失败")
except NetworkError as e:
    # 网络问题
    pass
```

### 模式3：高级客户端

```python
from auauth import AuthClient, AuthConfig

config = AuthConfig(
    gateway_ip="192.168.10.1",
    license_path="license.lic",
    timeout=10,
    debug=True
)

client = AuthClient(config)
result = client.authorize()
```

---

## 常量

### 默认值

| 常量 | 值 | 说明 |
|------|-----|------|
| DEFAULT_ADMIN_ACCOUNT | "CMCCAdmin" | 默认管理员账号 |
| DEFAULT_ADMIN_PASSWORD | "aDm8H%MdA" | 默认管理员密码 |
| DEFAULT_GATEWAY_PORT | 23 | 默认Telnet端口 |
| DEFAULT_TIMEOUT | 5 | 默认HTTP超时 |
