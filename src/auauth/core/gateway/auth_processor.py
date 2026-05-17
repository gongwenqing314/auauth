"""
网关授权处理器
实现与网关API的7步授权交互流程
"""
import json
import time
import requests
import base64
from dataclasses import dataclass
from typing import Optional, Dict, Any
from urllib.parse import urljoin

from ..crypto.sm2_crypto import SM2Crypto
from ..crypto.aes_crypto import AESCrypto
from ..license import LicenseInfo
from ..hardware import get_hardware_info


@dataclass
class AuthResult:
    """授权结果数据类"""
    success: bool = False
    message: str = ""
    access_user: str = ""
    access_password: str = ""
    telnet_address: str = ""
    telnet_port: str = ""
    telnet_connected: bool = False
    
    def __str__(self) -> str:
        return (f"AuthResult(success={self.success}, message='{self.message}', "
                f"access_user='{self.access_user}', telnet_address='{self.telnet_address}', "
                f"telnet_port='{self.telnet_port}')")


class GatewayAuthProcessor:
    """网关授权处理器"""
    
    def __init__(self, 
                 gateway_url: str,
                 license_info: LicenseInfo,
                 admin_account: str,
                 admin_password: str,
                 local_ip: str = "",
                 public_key2_path: str = "license/public_key2.pem",
                 timeout: int = 5,
                 debug: bool = False):
        self.gateway_url = gateway_url
        self.license_info = license_info
        self.admin_account = admin_account
        self.admin_password = admin_password
        self.local_ip = local_ip
        self.timeout = timeout
        self.debug = debug
        
        # 初始化SM2加密器
        self.sm2_crypto = SM2Crypto(public_key2_path)
        
        # 预热：提前获取硬件信息（避免在授权流程中首次调用wmic/PowerShell耗时操作）
        # 以及预热SM2加密（首次调用可能较慢）
        print("预热硬件信息和加密模块...")
        hw = get_hardware_info()
        self._hardware_fingerprint = hw.mac_address.replace(":", "").replace("-", "").upper() + "GATEWAY"
        # 预热SM2加密（执行一次空加密来初始化内部状态）
        self._sm2_encrypt_and_base64("warmup")
        print(f"硬件指纹: {self._hardware_fingerprint}")
        
        # 会话状态
        self.rand_a: str = ""
        self.rand_b: str = ""
        self.gateway_timestamp: int = 0
        
        # 使用HTTP Session（连接池复用，减少TCP握手开销）
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
    
    def _log(self, msg: str):
        """调试日志输出"""
        if self.debug:
            print(msg)
    
    def _sm2_encrypt_and_base64(self, plaintext: str) -> str:
        """
        使用SM2加密并返回Base64编码结果
        与Java的 Base64.toBase64String(encryptWithPublicKey2(data)) 完全一致
        """
        encrypted = self.sm2_crypto.encrypt(plaintext)
        return base64.b64encode(encrypted).decode('utf-8')
    
    def execute_auth_flow(self) -> AuthResult:
        """执行完整的授权流程（步骤2-7）"""
        try:
            print("开始执行网关授权流程...")
            result = AuthResult()
            
            if not self._send_auth_init():
                return AuthResult(False, "步骤2：提交基础验证信息失败，请检查账号密码信息")
            
            # 步骤3→4之间立即发送，不做任何多余操作
            if not self._send_encrypt_rand_a():
                return AuthResult(False, "步骤4：加密随机数A失败")
            
            if not self._send_encrypt_rand_b(result):
                return AuthResult(False, "步骤6：加密随机数B失败")
            
            print("授权流程完成")
            result.success = True
            result.message = "授权成功"
            return result
            
        except Exception as e:
            print(f"授权流程执行异常: {e}")
            import traceback
            traceback.print_exc()
            return AuthResult(False, f"授权流程异常: {str(e)}")
        finally:
            # 关闭HTTP Session
            self.session.close()
    
    def _send_auth_init(self) -> bool:
        """步骤2：提交基础验证信息"""
        try:
            print("=" * 60)
            print("步骤2：提交基础验证信息...")
            print("=" * 60)
            
            t_start = time.time()
            data = {}
            
            # 1. 加密管理员账号
            data["adminAccount"] = self._sm2_encrypt_and_base64(self.admin_account)
            
            # 2. 加密管理员密码
            data["adminPassword"] = self._sm2_encrypt_and_base64(self.admin_password)
            
            # 3. 生成AES密钥并加密
            aes_key = AESCrypto.generate_key(16)
            data["aesKey"] = self._sm2_encrypt_and_base64(aes_key)
            
            # 4. AES加密许可证文件
            data["licFile"] = AESCrypto.encrypt_bytes(
                self.license_info.license_file_data, 
                aes_key
            )
            
            # 5. 加密收集类型
            data["collectType"] = self._sm2_encrypt_and_base64("Telnet")
            
            # 6. 加密硬件指纹（使用预热的值）
            data["hardwareFingerprint"] = self._sm2_encrypt_and_base64(self._hardware_fingerprint)
            
            # 7. 时间戳
            data["timestamp"] = int(time.time() * 1000)
            
            t_prepare = time.time()
            self._log(f"[DEBUG] 步骤2准备耗时: {t_prepare - t_start:.3f}秒")
            
            # 构建请求体
            request_data = {
                "interfaceId": "auth.init",
                "data": data
            }
            
            # 发送请求
            self._log(f"[DEBUG] 发送POST请求到: {self.gateway_url}")
            response = self._send_post_request(request_data)
            
            if not response:
                print("步骤2：无响应")
                return False
            
            t_response = time.time()
            self._log(f"[DEBUG] 步骤2 HTTP往返耗时: {t_response - t_prepare:.3f}秒")
            
            # 检查错误码
            if "code" in response:
                code = response.get("code")
                error_codes = ["4001", "4002", "4003", "4004", "4005", "4006", "4007"]
                if str(code) in error_codes:
                    error_msg = response.get("msg", "未知错误")
                    print(f"步骤2失败: {error_msg} (错误码: {code})")
                    return False
            
            if (response.get("interfaceId") == "auth.sendRandA" and 
                response.get("code") == 200):
                
                response_data = response.get("data", {})
                self.rand_a = response_data.get("randA", "")
                self.gateway_timestamp = response_data.get("timestamp", 0)
                
                print(f"步骤2成功，获取到随机数A: {self.rand_a}")
                print(f"  网关timestamp: {self.gateway_timestamp}")
                return True
            else:
                error_msg = response.get("msg", "未知错误")
                print(f"步骤2失败: {error_msg}")
                return False
                
        except Exception as e:
            print(f"步骤2执行异常: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _send_encrypt_rand_a(self) -> bool:
        """步骤4：加密随机数A（收到步骤3响应后立即执行）"""
        try:
            print("\n" + "=" * 60)
            print("步骤4：加密随机数A...")
            print("=" * 60)
            
            t_start = time.time()
            
            # 立即加密randA并发送，不做多余操作
            encrypted_rand_a = self._sm2_encrypt_and_base64(self.rand_a)
            
            data = {
                "encryptedRandA": encrypted_rand_a,
                "timestamp": self.gateway_timestamp,
                "requestTimestamp": int(time.time() * 1000)
            }
            
            t_prepare = time.time()
            self._log(f"[DEBUG] 步骤4准备耗时: {t_prepare - t_start:.3f}秒")
            
            request_data = {
                "interfaceId": "auth.encryptRandA",
                "data": data
            }
            
            response = self._send_post_request(request_data)
            
            if not response:
                print("步骤4：无响应")
                return False
            
            t_response = time.time()
            self._log(f"[DEBUG] 步骤4 HTTP往返耗时: {t_response - t_prepare:.3f}秒")
            
            if (response.get("interfaceId") == "auth.sendRandB" and 
                response.get("code") == 200):
                
                response_data = response.get("data", {})
                self.rand_b = response_data.get("randB", "")
                
                print(f"步骤4成功，获取到随机数B: {self.rand_b}")
                return True
            else:
                error_msg = response.get("msg", "未知错误")
                print(f"步骤4失败: {error_msg}")
                return False
                
        except Exception as e:
            print(f"步骤4执行异常: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _send_encrypt_rand_b(self, result: AuthResult) -> bool:
        """步骤6：加密随机数B"""
        try:
            print("\n" + "=" * 60)
            print("步骤6：加密随机数B...")
            print("=" * 60)
            
            encrypted_rand_b = self._sm2_encrypt_and_base64(self.rand_b)
            
            data = {
                "encryptedRandB": encrypted_rand_b,
                "timestamp": self.gateway_timestamp,
                "requestTimestamp": int(time.time() * 1000)
            }
            
            request_data = {
                "interfaceId": "auth.encryptRandB",
                "data": data
            }
            
            response = self._send_post_request(request_data)
            
            if not response:
                print("步骤6：无响应")
                return False
            
            if (response.get("interfaceId") == "auth.authResult" and 
                response.get("code") == 200):
                
                result_data = response.get("data", {})
                result.access_user = result_data.get("accessUser", "")
                result.access_password = result_data.get("accessPassword", "")
                
                print("步骤6成功，获取到授权结果:")
                print(f"  访问用户: {result.access_user}")
                print(f"  访问密码: {result.access_password}")
                
                return True
            else:
                error_msg = response.get("msg", "未知错误")
                print(f"步骤6失败: {error_msg}")
                return False
                
        except Exception as e:
            print(f"步骤6执行异常: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _send_post_request(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """发送POST请求（使用Session连接池）"""
        try:
            json_data = json.dumps(data, ensure_ascii=False)
            
            self._log(f"[DEBUG] 请求体长度: {len(json_data)} 字节")
            
            response = self.session.post(
                self.gateway_url,
                data=json_data.encode('utf-8'),
                timeout=self.timeout
            )
            
            self._log(f"[DEBUG] HTTP状态码: {response.status_code}")
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"HTTP错误码: {response.status_code}")
                print(f"响应内容: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            print(f"请求超时（{self.timeout}秒）")
            return None
        except requests.exceptions.ConnectionError as e:
            print(f"连接错误: {e}")
            return None
        except Exception as e:
            print(f"请求异常: {e}")
            return None


def execute_gateway_auth(
    gateway_address: str,
    gateway_port: str,
    admin_account: str,
    admin_password: str,
    license_info: LicenseInfo,
    local_ip: str = "",
    public_key2_path: str = "license/public_key2.pem",
    debug: bool = False
) -> AuthResult:
    """执行网关授权的便捷函数"""
    gateway_url = f"http://{gateway_address}/cmdc_tool_access_auth.html"
    
    print(f"网关API地址: {gateway_url}")
    
    processor = GatewayAuthProcessor(
        gateway_url=gateway_url,
        license_info=license_info,
        admin_account=admin_account,
        admin_password=admin_password,
        local_ip=local_ip,
        public_key2_path=public_key2_path,
        debug=debug
    )
    
    result = processor.execute_auth_flow()
    
    if result.success:
        result.telnet_address = gateway_address
        result.telnet_port = gateway_port
    
    return result


if __name__ == "__main__":
    print("网关授权处理器模块")
    print("请通过GUI或主程序调用此模块")
