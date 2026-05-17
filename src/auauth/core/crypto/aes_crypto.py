"""
AES加密模块
实现AES/ECB/PKCS5Padding加密，与Java版本兼容
"""
import base64
import secrets
import string
from typing import Union
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


class AESCrypto:
    """AES加密类"""
    
    # 默认密钥（与Java版本一致）
    DEFAULT_KEY = "abcdefg123456789"
    # 算法模式
    ALGORITHM = "AES"
    MODE = AES.MODE_ECB
    
    @staticmethod
    def encrypt(plaintext: Union[str, bytes], key: str = None) -> str:
        """
        AES加密并返回Base64编码的结果
        
        Args:
            plaintext: 待加密的明文
            key: 加密密钥，默认使用DEFAULT_KEY
            
        Returns:
            Base64编码的加密结果
        """
        if key is None:
            key = AESCrypto.DEFAULT_KEY
        
        if isinstance(plaintext, str):
            plaintext = plaintext.encode('utf-8')
        
        # 创建AES加密器
        cipher = AES.new(key.encode('utf-8'), AESCrypto.MODE)
        
        # PKCS5填充
        padded_data = pad(plaintext, AES.block_size)
        
        # 加密
        encrypted = cipher.encrypt(padded_data)
        
        # Base64编码
        return base64.b64encode(encrypted).decode('utf-8')
    
    @staticmethod
    def decrypt(ciphertext: str, key: str = None) -> str:
        """
        解密Base64编码的密文
        
        Args:
            ciphertext: Base64编码的密文
            key: 解密密钥，默认使用DEFAULT_KEY
            
        Returns:
            解密后的明文
        """
        if key is None:
            key = AESCrypto.DEFAULT_KEY
        
        # 处理URL编码的+号
        ciphertext = ciphertext.replace(' ', '+')
        
        # Base64解码
        encrypted = base64.b64decode(ciphertext)
        
        # 创建AES解密器
        cipher = AES.new(key.encode('utf-8'), AESCrypto.MODE)
        
        # 解密
        decrypted = cipher.decrypt(encrypted)
        
        # 去除PKCS5填充
        plaintext = unpad(decrypted, AES.block_size)
        
        return plaintext.decode('utf-8')
    
    @staticmethod
    def encrypt_bytes(data: bytes, key: str) -> str:
        """
        加密字节数组并返回Base64编码的结果
        
        Args:
            data: 待加密的字节数据
            key: 加密密钥
            
        Returns:
            Base64编码的加密结果
        """
        # 创建AES加密器
        cipher = AES.new(key.encode('utf-8'), AESCrypto.MODE)
        
        # PKCS5填充
        padded_data = pad(data, AES.block_size)
        
        # 加密
        encrypted = cipher.encrypt(padded_data)
        
        # Base64编码
        return base64.b64encode(encrypted).decode('utf-8')
    
    @staticmethod
    def decrypt_bytes(ciphertext: str, key: str) -> bytes:
        """
        解密Base64编码的密文，返回字节数组
        
        Args:
            ciphertext: Base64编码的密文
            key: 解密密钥
            
        Returns:
            解密后的字节数据
        """
        # 处理URL编码的+号
        ciphertext = ciphertext.replace(' ', '+')
        
        # Base64解码
        encrypted = base64.b64decode(ciphertext)
        
        # 创建AES解密器
        cipher = AES.new(key.encode('utf-8'), AESCrypto.MODE)
        
        # 解密
        decrypted = cipher.decrypt(encrypted)
        
        # 去除PKCS5填充
        return unpad(decrypted, AES.block_size)
    
    @staticmethod
    def generate_key(length: int = 16) -> str:
        """
        生成随机AES密钥
        
        Args:
            length: 密钥长度，默认16字节（128位）
            
        Returns:
            随机生成的密钥字符串
        """
        characters = string.ascii_letters + string.digits
        return ''.join(secrets.choice(characters) for _ in range(length))
    
    @staticmethod
    def encrypt_bytes_to_bytes(data: bytes, key: str) -> bytes:
        """
        加密字节数组并返回字节结果
        
        Args:
            data: 待加密的字节数据
            key: 加密密钥
            
        Returns:
            加密后的字节数据
        """
        # 创建AES加密器
        cipher = AES.new(key.encode('utf-8'), AESCrypto.MODE)
        
        # PKCS5填充
        padded_data = pad(data, AES.block_size)
        
        # 加密
        return cipher.encrypt(padded_data)


# 便捷函数
def aes_encrypt(plaintext: Union[str, bytes], key: str = None) -> str:
    """AES加密便捷函数"""
    return AESCrypto.encrypt(plaintext, key)


def aes_decrypt(ciphertext: str, key: str = None) -> str:
    """AES解密便捷函数"""
    return AESCrypto.decrypt(ciphertext, key)


def aes_encrypt_bytes(data: bytes, key: str) -> str:
    """AES加密字节数组便捷函数"""
    return AESCrypto.encrypt_bytes(data, key)


def aes_decrypt_bytes(ciphertext: str, key: str) -> bytes:
    """AES解密字节数组便捷函数"""
    return AESCrypto.decrypt_bytes(ciphertext, key)


if __name__ == "__main__":
    # 测试
    test_data = "Hello, AES!"
    
    # 使用默认密钥加密
    encrypted = AESCrypto.encrypt(test_data)
    print(f"加密结果: {encrypted}")
    
    # 解密
    decrypted = AESCrypto.decrypt(encrypted)
    print(f"解密结果: {decrypted}")
    
    # 使用自定义密钥
    custom_key = "mysecretkey12345"
    encrypted2 = AESCrypto.encrypt(test_data, custom_key)
    print(f"自定义密钥加密: {encrypted2}")
    decrypted2 = AESCrypto.decrypt(encrypted2, custom_key)
    print(f"自定义密钥解密: {decrypted2}")
    
    # 生成随机密钥
    random_key = AESCrypto.generate_key()
    print(f"随机密钥: {random_key}")
