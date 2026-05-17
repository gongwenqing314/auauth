"""
AuAuth - 设备授权库

用于网关设备的SM2/SM3授权认证，支持许可证验证和Telnet授权流程。
只需安装一个包即可使用。

基本用法:
    >>> from auauth import authorize_device
    >>> result = authorize_device(
    ...     gateway_ip="192.168.10.1",
    ...     license_file="license.lic"
    ... )
    >>> if result.success:
    ...     print(f"授权成功: {result.access_user}/{result.access_password}")

高级用法:
    >>> from auauth import AuthClient, AuthConfig
    >>> config = AuthConfig(gateway_ip="192.168.10.1", license_path="license.lic")
    >>> client = AuthClient(config)
    >>> result = client.authorize()

异常处理:
    >>> from auauth import authorize_device, LicenseError, AuthFlowError
    >>> try:
    ...     result = authorize_device(...)
    ... except LicenseError as e:
    ...     print(f"许可证错误: {e}")
    ... except AuthFlowError as e:
    ...     print(f"授权流程错误(步骤{e.step}): {e}")
"""

__version__ = "1.0.0"
__author__ = "AuTool Team"

# 主要API
from .api import (
    authorize_device,
    AuthClient,
    AuthConfig,
    AuthResult,
)

# 异常类
from .exceptions import (
    AuAuthError,
    LicenseError,
    AuthFlowError,
    NetworkError,
    CryptoError,
)

# 核心模块（供高级用户直接使用）
from .core.license import LicenseValidator, LicenseInfo
from .core.gateway.auth_processor import (
    GatewayAuthProcessor,
    AuthResult as InternalAuthResult,
    execute_gateway_auth,
)
from .core.hardware import get_hardware_info

__all__ = [
    # 主要API
    "authorize_device",
    "AuthClient",
    "AuthConfig",
    "AuthResult",
    # 异常
    "AuAuthError",
    "LicenseError",
    "AuthFlowError",
    "NetworkError",
    "CryptoError",
    # 核心模块
    "LicenseValidator",
    "LicenseInfo",
    "GatewayAuthProcessor",
    "execute_gateway_auth",
    "get_hardware_info",
]
