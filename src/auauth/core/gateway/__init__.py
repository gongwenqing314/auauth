"""
网关授权模块
包含与网关API交互的授权流程处理器
"""
from .auth_processor import GatewayAuthProcessor, AuthResult

__all__ = ['GatewayAuthProcessor', 'AuthResult']
