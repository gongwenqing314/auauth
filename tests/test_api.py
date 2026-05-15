"""
API测试用例
"""
import pytest
from pathlib import Path

from auauth import AuthConfig, AuthResult
from auauth.exceptions import ConfigError, LicenseError


class TestAuthConfig:
    """测试AuthConfig"""
    
    def test_valid_config(self):
        """测试有效配置"""
        # 注意：这个测试需要一个真实的许可证文件
        # 这里使用pytest的tmp_path创建一个临时文件
        pass  # 需要实际许可证文件才能测试
    
    def test_empty_gateway_ip(self):
        """测试空网关IP"""
        with pytest.raises(ConfigError):
            AuthConfig(
                gateway_ip="",
                license_path="license.lic"
            )
    
    def test_nonexistent_license(self):
        """测试不存在的许可证文件"""
        with pytest.raises(LicenseError):
            AuthConfig(
                gateway_ip="192.168.10.1",
                license_path="/nonexistent/path/license.lic"
            )


class TestAuthResult:
    """测试AuthResult"""
    
    def test_success_result(self):
        """测试成功结果"""
        result = AuthResult(
            success=True,
            message="授权成功",
            access_user="testuser",
            access_password="testpass",
            telnet_address="192.168.10.1",
            telnet_port=23
        )
        
        assert result.success is True
        assert result.access_user == "testuser"
        
        creds = result.get_telnet_credentials()
        assert creds is not None
        assert creds["host"] == "192.168.10.1"
        assert creds["port"] == 23
        assert creds["username"] == "testuser"
        assert creds["password"] == "testpass"
    
    def test_failed_result(self):
        """测试失败结果"""
        result = AuthResult(
            success=False,
            message="授权失败"
        )
        
        assert result.success is False
        assert result.get_telnet_credentials() is None


class TestAuthorizeDevice:
    """测试authorize_device函数"""
    
    def test_function_exists(self):
        """测试函数存在"""
        from auauth import authorize_device
        assert callable(authorize_device)
