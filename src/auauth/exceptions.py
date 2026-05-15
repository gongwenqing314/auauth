"""
AuAuth 异常定义模块

定义了库中使用的所有自定义异常类，便于调用者进行精确的错误处理。
"""


class AuAuthError(Exception):
    """
    AuAuth基础异常类
    
    所有AuAuth相关异常的基类。捕获此异常可捕获库中所有自定义异常。
    
    Example:
        >>> from auauth import authorize_device, AuAuthError
        >>> try:
        ...     result = authorize_device(...)
        ... except AuAuthError as e:
        ...     print(f"授权错误: {e}")
    """
    pass


class LicenseError(AuAuthError):
    """
    许可证相关错误
    
    包括：
    - 许可证文件不存在
    - 许可证格式错误
    - 许可证已过期
    - 许可证硬件指纹不匹配
    - 许可证签名验证失败
    
    Attributes:
        license_path: 许可证文件路径
    
    Example:
        >>> from auauth import authorize_device, LicenseError
        >>> try:
        ...     result = authorize_device(license_file="invalid.lic")
        ... except LicenseError as e:
        ...     print(f"许可证错误: {e}")
    """
    def __init__(self, message: str, license_path: str = None):
        super().__init__(message)
        self.license_path = license_path


class AuthFlowError(AuAuthError):
    """
    授权流程错误
    
    在7步授权流程中的某一步失败时抛出。
    
    Attributes:
        step: 失败的步骤编号（2, 4, 6对应auth.init, auth.encryptRandA, auth.encryptRandB）
        code: 网关返回的错误码（如"4001", "4005"等）
        message: 错误描述
    
    Example:
        >>> from auauth import authorize_device, AuthFlowError
        >>> try:
        ...     result = authorize_device(...)
        ... except AuthFlowError as e:
        ...     print(f"步骤{e.step}失败: {e.message} (错误码: {e.code})")
    """
    def __init__(self, message: str, step: int, code: str = None):
        super().__init__(message)
        self.step = step
        self.code = code
        self.message = message


class NetworkError(AuAuthError):
    """
    网络连接错误
    
    包括：
    - 连接超时
    - 连接被拒绝
    - DNS解析失败
    - HTTP错误响应
    
    Attributes:
        url: 请求的URL
        status_code: HTTP状态码（如果有）
    
    Example:
        >>> from auauth import authorize_device, NetworkError
        >>> try:
        ...     result = authorize_device(gateway_ip="192.168.10.1")
        ... except NetworkError as e:
        ...     print(f"网络错误: {e}")
        ...     if e.status_code:
        ...         print(f"HTTP状态码: {e.status_code}")
    """
    def __init__(self, message: str, url: str = None, status_code: int = None):
        super().__init__(message)
        self.url = url
        self.status_code = status_code


class CryptoError(AuAuthError):
    """
    加密/解密错误
    
    包括：
    - SM2加密失败
    - SM2解密失败
    - AES加密失败
    - 密钥格式错误
    - ASN.1编码/解码错误
    
    Example:
        >>> from auauth import authorize_device, CryptoError
        >>> try:
        ...     result = authorize_device(...)
        ... except CryptoError as e:
        ...     print(f"加密错误: {e}")
    """
    pass


class ConfigError(AuAuthError):
    """
    配置错误
    
    参数配置不正确时抛出，如缺少必需参数、参数格式错误等。
    
    Example:
        >>> from auauth import AuthConfig
        >>> try:
        ...     config = AuthConfig(gateway_ip="")  # 空IP
        ... except ConfigError as e:
        ...     print(f"配置错误: {e}")
    """
    pass
