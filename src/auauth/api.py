"""
AuAuth 主要API模块

提供简洁的授权接口，包括：
- authorize_device: 一行代码完成授权
- AuthClient: 高级客户端，支持更多配置
- AuthConfig: 配置类
- AuthResult: 授权结果
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from pathlib import Path
import os

# 导入核心模块（内置在auauth包内）
from .core.license import LicenseValidator, LicenseInfo
from .core.gateway.auth_processor import (
    GatewayAuthProcessor, 
    AuthResult as _InternalAuthResult,
    execute_gateway_auth as _execute_gateway_auth
)
from .core.hardware import get_hardware_info

from .exceptions import (
    AuAuthError,
    LicenseError,
    AuthFlowError,
    NetworkError,
    CryptoError,
    ConfigError,
)


@dataclass
class AuthConfig:
    """
    授权配置类
    
    封装授权所需的全部配置参数。
    
    Attributes:
        gateway_ip: 网关IP地址（必需）
        license_path: 许可证文件路径（必需）
        admin_account: 管理员账号（默认: CMCCAdmin）
        admin_password: 管理员密码（默认: aDm8H%MdA）
        gateway_port: 网关Telnet端口（默认: 23）
        public_key_path: 公钥文件路径（默认使用内置）
        timeout: HTTP请求超时秒数（默认: 5）
        debug: 是否输出调试信息（默认: False）
    
    Example:
        >>> config = AuthConfig(
        ...     gateway_ip="192.168.10.1",
        ...     license_path="/path/to/license.lic",
        ...     admin_account="CMCCAdmin",
        ...     admin_password="aDm8H%MdA"
        ... )
    """
    gateway_ip: str
    license_path: str
    admin_account: str = "CMCCAdmin"
    admin_password: str = "aDm8H%MdA"
    gateway_port: int = 23
    public_key_path: Optional[str] = None
    timeout: int = 5
    debug: bool = False
    
    def __post_init__(self):
        """验证配置"""
        if not self.gateway_ip:
            raise ConfigError("gateway_ip不能为空")
        if not self.license_path:
            raise ConfigError("license_path不能为空")
        if not Path(self.license_path).exists():
            raise LicenseError(f"许可证文件不存在: {self.license_path}", self.license_path)


@dataclass
class AuthResult:
    """
    授权结果类
    
    包含授权流程的完整结果和Telnet连接信息。
    
    Attributes:
        success: 授权是否成功
        message: 结果消息（成功或失败原因）
        access_user: 授权后的访问用户名（成功时有效）
        access_password: 授权后的访问密码（成功时有效）
        telnet_address: Telnet连接地址（成功时有效）
        telnet_port: Telnet连接端口（成功时有效）
        raw_result: 内部原始结果对象
    
    Example:
        >>> result = authorize_device(...)
        >>> if result.success:
        ...     print(f"连接Telnet: {result.telnet_address}:{result.telnet_port}")
        ...     print(f"账号: {result.access_user}, 密码: {result.access_password}")
    """
    success: bool
    message: str = ""
    access_user: str = ""
    access_password: str = ""
    telnet_address: str = ""
    telnet_port: int = 23
    raw_result: Any = None
    
    def get_telnet_credentials(self) -> Optional[Dict[str, str]]:
        """
        获取Telnet连接凭证
        
        Returns:
            包含host, port, username, password的字典，授权失败时返回None
        
        Example:
            >>> result = authorize_device(...)
            >>> creds = result.get_telnet_credentials()
            >>> if creds:
            ...     tn = telnetlib.Telnet(creds['host'], creds['port'])
            ...     tn.read_until(b"login: ")
            ...     tn.write(creds['username'].encode() + b"\n")
        """
        if not self.success:
            return None
        return {
            "host": self.telnet_address,
            "port": self.telnet_port,
            "username": self.access_user,
            "password": self.access_password,
        }


class AuthClient:
    """
    授权客户端
    
    高级API，支持更多控制和复用。
    
    Example:
        >>> from auauth import AuthClient, AuthConfig
        >>> 
        >>> # 创建配置
        >>> config = AuthConfig(
        ...     gateway_ip="192.168.10.1",
        ...     license_path="license.lic"
        >>> )
        >>> 
        >>> # 创建客户端并授权
        >>> client = AuthClient(config)
        >>> result = client.authorize()
        >>> 
        >>> if result.success:
        ...     print("授权成功")
    """
    
    def __init__(self, config: AuthConfig):
        """
        初始化授权客户端
        
        Args:
            config: 授权配置对象
        """
        self.config = config
        self._processor: Optional["GatewayAuthProcessor"] = None
        self._license_info: Optional["LicenseInfo"] = None
    
    def _load_license(self) -> "LicenseInfo":
        """加载并验证许可证"""
        try:
            public_key_path = self.config.public_key_path or os.path.join(os.path.dirname(__file__), "assets", "public_key.pem")
            validator = LicenseValidator(public_key_path)
            is_valid, license_info, error = validator.validate(self.config.license_path)

            if not is_valid:
                raise LicenseError(
                    f"许可证验证失败: {error}",
                    self.config.license_path
                )

            return license_info
        except Exception as e:
            if isinstance(e, LicenseError):
                raise
            raise LicenseError(f"许可证加载失败: {e}", self.config.license_path)
    
    def authorize(self) -> AuthResult:
        """
        执行授权流程
        
        Returns:
            AuthResult: 授权结果
        
        Raises:
            LicenseError: 许可证验证失败
            AuthFlowError: 授权流程某步骤失败
            NetworkError: 网络连接错误
            CryptoError: 加密/解密错误
        """
        try:
            # 加载许可证
            self._license_info = self._load_license()
            
            # 确定公钥路径
            public_key_path = self.config.public_key_path
            if public_key_path is None:
                public_key_path = os.path.join(os.path.dirname(__file__), "assets", "public_key2.pem")
            
            # 执行授权
            internal_result = _execute_gateway_auth(
                gateway_address=self.config.gateway_ip,
                gateway_port=str(self.config.gateway_port),
                admin_account=self.config.admin_account,
                admin_password=self.config.admin_password,
                license_info=self._license_info,
                public_key2_path=public_key_path
            )
            
            # 转换为标准结果
            result = AuthResult(
                success=internal_result.success,
                message=internal_result.message,
                access_user=internal_result.access_user,
                access_password=internal_result.access_password,
                telnet_address=internal_result.telnet_address,
                telnet_port=int(internal_result.telnet_port) if internal_result.telnet_port else 23,
                raw_result=internal_result
            )
            
            # 检查是否成功
            if not result.success:
                # 尝试从消息中解析步骤和错误码
                step = 0
                code = None
                if "步骤2" in result.message:
                    step = 2
                elif "步骤4" in result.message:
                    step = 4
                elif "步骤6" in result.message:
                    step = 6
                
                raise AuthFlowError(result.message, step, code)
            
            return result
            
        except (LicenseError, AuthFlowError):
            raise
        except Exception as e:
            # 分类其他异常
            error_str = str(e).lower()
            if "timeout" in error_str or "connection" in error_str:
                raise NetworkError(f"网络错误: {e}")
            elif "encrypt" in error_str or "decrypt" in error_str or "crypto" in error_str:
                raise CryptoError(f"加密错误: {e}")
            else:
                raise AuAuthError(f"授权失败: {e}")


def authorize_device(
    gateway_ip: str,
    license_file: str,
    admin_account: str = "CMCCAdmin",
    admin_password: str = "aDm8H%MdA",
    gateway_port: int = 23,
    public_key_file: Optional[str] = None,
    timeout: int = 5,
    debug: bool = False
) -> AuthResult:
    """
    设备授权（一行代码完成授权）
    
    最简化的授权接口，传入必要参数即可完成授权。
    
    Args:
        gateway_ip: 网关IP地址（必需）
        license_file: 许可证文件路径（必需）
        admin_account: 管理员账号（默认: CMCCAdmin）
        admin_password: 管理员密码（默认: aDm8H%MdA）
        gateway_port: 网关Telnet端口（默认: 23）
        public_key_file: 公钥文件路径（默认使用内置）
        timeout: HTTP请求超时秒数（默认: 5）
        debug: 是否输出调试信息（默认: False）
    
    Returns:
        AuthResult: 授权结果，包含success标志和Telnet连接信息
    
    Raises:
        LicenseError: 许可证验证失败（文件不存在、格式错误、已过期等）
        AuthFlowError: 授权流程失败（某步骤返回错误码）
        NetworkError: 网络连接错误
        CryptoError: 加密/解密错误
    
    Example:
        >>> from auauth import authorize_device
        >>> 
        >>> # 基本用法
        >>> result = authorize_device(
        ...     gateway_ip="192.168.10.1",
        ...     license_file="/path/to/license.lic"
        ... )
        >>> 
        >>> if result.success:
        ...     print(f"授权成功!")
        ...     creds = result.get_telnet_credentials()
        ...     # 使用creds连接Telnet...
        ... else:
        ...     print(f"授权失败: {result.message}")
        
        >>> # 完整参数
        >>> result = authorize_device(
        ...     gateway_ip="192.168.10.1",
        ...     license_file="license.lic",
        ...     admin_account="CMCCAdmin",
        ...     admin_password="aDm8H%MdA",
        ...     gateway_port=23
        ... )
    
    Note:
        此函数是阻塞的，会等待授权流程完成（通常需要5-10秒）。
        如果需要在GUI中异步调用，请考虑使用线程或asyncio包装。
    """
    config = AuthConfig(
        gateway_ip=gateway_ip,
        license_path=license_file,
        admin_account=admin_account,
        admin_password=admin_password,
        gateway_port=gateway_port,
        public_key_path=public_key_file,
        timeout=timeout,
        debug=debug
    )
    
    client = AuthClient(config)
    return client.authorize()
