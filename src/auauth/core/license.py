"""
许可证解析与验证模块
用于解析许可证文件、验证签名、检查有效期等
"""
import os
import sys
import tarfile
import tempfile
import shutil
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional, Dict
from pathlib import Path

from .crypto.sm2_crypto import verify_sm2_signature, load_public_key_from_pem
from .hardware import get_hardware_info


@dataclass
class LicenseInfo:
    """许可证信息数据类"""
    cpu_id: str = ""
    product_type: str = ""
    mac: str = ""
    disk_serial: str = ""
    request_version: str = ""
    request_days: str = ""
    start_time: str = ""
    vendor: str = ""
    access_type: str = ""
    
    # 文件路径
    license_file: str = ""
    data_file: str = ""
    signature_file: str = ""
    public_key_file: str = ""
    
    # 文件数据
    license_file_data: bytes = field(default_factory=lambda: b"")
    data_file_data: bytes = field(default_factory=lambda: b"")
    signature_file_data: bytes = field(default_factory=lambda: b"")
    public_key_data: bytes = field(default_factory=lambda: b"")
    
    # 验证状态
    verified: bool = False


class LicenseValidator:
    """许可证验证器"""
    
    def __init__(self, public_key_path: str = "../assets/public_key.pem"):
        """
        初始化验证器
        
        Args:
            public_key_path: 签名验证公钥路径
        """
        # 处理打包后的资源路径
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller 打包后的路径
            base_path = sys._MEIPASS
            public_key_path = os.path.join(base_path, public_key_path)
        else:
            # 开发环境路径
            if not os.path.isabs(public_key_path):
                public_key_path = os.path.join(os.path.dirname(__file__), public_key_path)
        
        self.public_key_path = public_key_path
        self.temp_dir: Optional[str] = None
    
    def parse_license(self, license_file_path: str) -> Optional[LicenseInfo]:
        """
        解析许可证文件
        
        与Java代码保持一致的逻辑：
        1. 解压到临时目录
        2. 读取所有数据到内存
        3. 读取完成后不立即删除临时目录（由调用方负责清理）
        
        Args:
            license_file_path: 许可证文件路径（.lic文件，实际是tar归档）
            
        Returns:
            LicenseInfo对象，解析失败返回None
        """
        try:
            # 转换为绝对路径
            abs_license_path = os.path.abspath(license_file_path)
            
            # 创建临时目录
            self.temp_dir = os.path.join(
                tempfile.gettempdir(), 
                f"license_{int(os.path.getmtime(abs_license_path) * 1000) if os.path.exists(abs_license_path) else id(self)}"
            )
            
            # 创建临时目录
            if not os.path.exists(self.temp_dir):
                os.makedirs(self.temp_dir)
            
            # 清空临时目录（与Java的cleanDirectory一致）
            self._clean_directory(self.temp_dir)
            
            # 解压许可证文件
            if not self._extract_license(abs_license_path, self.temp_dir):
                return None
            
            # data.txt路径
            data_file_path = os.path.join(self.temp_dir, "data.txt")
            # signature.bin路径
            signature_file_path = os.path.join(self.temp_dir, "signature.bin")
            
            # 检查文件是否存在
            if not os.path.exists(data_file_path):
                print(f"错误: 未找到data.txt文件: {data_file_path}")
                return None
            
            if not os.path.exists(signature_file_path):
                print(f"错误: 未找到signature.bin文件: {signature_file_path}")
                return None
            
            # 读取所有数据到内存（与Java一致）
            with open(abs_license_path, 'rb') as f:
                license_file_data = f.read()
            
            with open(data_file_path, 'rb') as f:
                data_file_data = f.read()
            
            with open(signature_file_path, 'rb') as f:
                signature_file_data = f.read()
            
            # 解析data.txt内容（用于显示）
            # data.txt可能包含中文，使用GBK编码
            try:
                data_content = data_file_data.decode('utf-8')
            except UnicodeDecodeError:
                data_content = data_file_data.decode('gbk', errors='replace')
            
            # 读取公钥
            public_key_data = b""
            abs_public_key_path = os.path.abspath(self.public_key_path)
            if os.path.exists(abs_public_key_path):
                public_key_data = load_public_key_from_pem(abs_public_key_path)
            
            # 解析属性
            props = self._parse_properties(data_content)
            
            # 创建LicenseInfo对象（与Java一致）
            info = LicenseInfo(
                cpu_id=props.get("CPU_ID", ""),
                product_type=props.get("PRODUCT_TYPE", ""),
                mac=props.get("MAC", ""),
                disk_serial=props.get("DISK_SERIAL", ""),
                request_version=props.get("REQUEST_VERSION", ""),
                request_days=props.get("REQUEST_DAYS", ""),
                start_time=props.get("START_TIME", ""),
                vendor=props.get("VENDOR", ""),
                access_type=props.get("ACCESS_TYPE", ""),
                license_file=abs_license_path,
                data_file=data_file_path,
                signature_file=signature_file_path,
                public_key_file=abs_public_key_path,
                license_file_data=license_file_data,
                data_file_data=data_file_data,
                signature_file_data=signature_file_data,
                public_key_data=public_key_data
            )
            
            print(f"许可证文件解析成功")
            print(f"  文件: {abs_license_path}")
            print(f"  产品类型: {info.product_type}")
            print(f"  CPU ID: {info.cpu_id}")
            print(f"  MAC: {info.mac}")
            print(f"  有效期: {info.start_time}, {info.request_days}天")
            
            return info
            
        except Exception as e:
            print(f"解析许可证文件失败: {e}")
            import traceback
            traceback.print_exc()
            return None
        # 注意：不在finally中清理临时目录，保持与Java一致
    
    def _extract_license(self, license_file_path: str, extract_dir: str) -> bool:
        """
        解压许可证文件
        
        Args:
            license_file_path: 许可证文件路径
            extract_dir: 解压目标目录
            
        Returns:
            解压是否成功
        """
        try:
            if not os.path.exists(license_file_path):
                print(f"错误: 许可证文件不存在: {license_file_path}")
                return False
            
            print(f"解压许可证文件: {license_file_path}")
            print(f"解压到: {extract_dir}")
            
            # 使用tarfile解压
            with tarfile.open(license_file_path, 'r') as tar:
                tar.extractall(path=extract_dir)
            
            print(f"许可证文件解压成功")
            return True
            
        except Exception as e:
            print(f"解压许可证文件失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _clean_directory(self, directory: str):
        """
        清空目录（与Java的cleanDirectory一致）
        """
        if os.path.exists(directory) and os.path.isdir(directory):
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                try:
                    if os.path.isfile(item_path):
                        os.unlink(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                except Exception as e:
                    print(f"清理文件失败: {item_path}, {e}")
    
    def _parse_properties(self, content: str) -> Dict[str, str]:
        """
        解析属性文件内容
        
        Args:
            content: 文件内容
            
        Returns:
            属性字典
        """
        props = {}
        for line in content.strip().split('\n'):
            # 保留原始行内容，不要strip（会丢失空格）
            original_line = line
            line = line.strip()
            if '=' in line:
                key, value = line.split('=', 1)
                props[key.strip()] = value.strip()
        return props
    
    def verify_signature(self, info: LicenseInfo) -> bool:
        """
        验证许可证签名
        
        Args:
            info: 许可证信息
            
        Returns:
            签名是否有效
        """
        try:
            if not os.path.exists(info.public_key_file):
                print(f"错误: 公钥文件不存在: {info.public_key_file}")
                return False
            
            if not info.data_file_data:
                print("错误: 数据文件内容为空")
                return False
            
            if not info.signature_file_data:
                print("错误: 签名文件内容为空")
                return False
            
            print("开始验证签名...")
            
            # 使用SM2验证签名
            result = verify_sm2_signature(
                info.data_file_data,
                info.signature_file_data,
                info.public_key_file
            )
            
            info.verified = result
            return result
            
        except Exception as e:
            print(f"签名验证失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def verify_hardware(self, info: LicenseInfo) -> tuple[bool, str]:
        """
        验证硬件指纹匹配
        
        Args:
            info: 许可证信息
            
        Returns:
            (是否匹配, 错误信息)
        """
        hw = get_hardware_info()
        
        print("验证硬件指纹...")
        print(f"  许可证CPU ID: {info.cpu_id}")
        print(f"  本机CPU ID: {hw.cpu_id}")
        print(f"  许可证MAC: {info.mac}")
        print(f"  本机MAC: {hw.mac}")
        
        # 验证CPU ID
        if info.cpu_id and info.cpu_id != hw.cpu_id:
            return False, f"CPU ID不匹配: 许可证={info.cpu_id}, 本机={hw.cpu_id}"
        
        # 验证磁盘序列号（使用包含匹配，因为许可证中可能有尾部空格或点号）
        info_disk = info.disk_serial.strip().rstrip('.')
        hw_disk = hw.disk_serial.strip()
        if info_disk and info_disk not in hw_disk and hw_disk not in info_disk:
            return False, f"磁盘序列号不匹配: 许可证={info_disk}, 本机={hw_disk}"
        
        print("硬件指纹验证通过")
        return True, ""
    
    def verify_validity(self, info: LicenseInfo) -> tuple[bool, str]:
        """
        验证许可证有效期
        
        Args:
            info: 许可证信息
            
        Returns:
            (是否有效, 错误信息)
        """
        try:
            if not info.start_time or not info.request_days:
                print("许可证无时间限制")
                return True, ""  # 无时间限制
            
            # 解析开始时间
            # 格式: 2026-04-30T12:00:00Z (ISO 8601)
            start_time = self._parse_datetime(info.start_time)
            if not start_time:
                return False, f"无法解析开始时间: {info.start_time}"
            
            # 解析有效天数
            try:
                request_days = int(info.request_days.strip())
                if request_days <= 0:
                    return False, "许可证有效天数必须大于0"
            except ValueError:
                return False, f"无效的有效天数: {info.request_days}"
            
            # 计算结束时间
            end_time = start_time + timedelta(days=request_days)
            
            # 获取当前时间（使用UTC）
            current_time = datetime.utcnow()
            
            print("验证有效期...")
            print(f"  开始时间: {start_time}")
            print(f"  当前时间: {current_time}")
            print(f"  结束时间: {end_time}")
            print(f"  有效天数: {request_days}")
            
            # 验证时间范围
            if current_time < start_time:
                return False, f"当前时间早于许可证生效时间: {info.start_time}"
            
            if current_time > end_time:
                return False, f"许可证已过期（有效期至: {end_time.strftime('%Y-%m-%d')}）"
            
            # 计算剩余天数
            days_remaining = (end_time - current_time).days
            if days_remaining <= 7:
                print(f"警告: 许可证将在 {days_remaining} 天后过期")
            else:
                print(f"许可证有效期验证通过，剩余 {days_remaining} 天")
            
            return True, ""
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, f"验证有效期时出错: {e}"
    
    def _parse_datetime(self, time_str: str) -> Optional[datetime]:
        """
        解析日期时间字符串
        
        Args:
            time_str: 时间字符串
            
        Returns:
            datetime对象，解析失败返回None
        """
        # 清理字符串
        time_str = time_str.strip()
        
        formats = [
            "%Y-%m-%dT%H:%M:%SZ",        # ISO 8601 UTC (2026-04-30T12:00:00Z)
            "%Y-%m-%dT%H:%M:%S%z",       # ISO 8601 with timezone
            "%Y-%m-%dT%H:%M:%S",        # ISO 8601 without timezone
            "%Y-%m-%d %H:%M:%S",         # Standard format
            "%Y-%m-%d",                   # Date only
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(time_str, fmt)
                # 如果是UTC时间(Z)，转换为本地时间
                if time_str.endswith('Z'):
                    # 假设UTC时间
                    from datetime import timezone
                    dt = dt.replace(tzinfo=timezone.utc)
                    return dt.replace(tzinfo=None)  # 返回不带时区的datetime
                return dt
            except ValueError:
                continue
        
        # 尝试处理带+08:00格式
        try:
            if '+' in time_str:
                parts = time_str.split('+')
                if len(parts) == 2 and ':' in parts[1]:
                    time_str_modified = parts[0]  # 忽略时区
                    dt = datetime.strptime(time_str_modified, "%Y-%m-%dT%H:%M:%S")
                    return dt
        except:
            pass
        
        return None
    
    def cleanup(self):
        """清理临时目录"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                print(f"临时目录已清理: {self.temp_dir}")
            except Exception as e:
                print(f"清理临时目录失败: {e}")
            self.temp_dir = None
    
    def validate(self, license_file_path: str) -> tuple[bool, Optional[LicenseInfo], str]:
        """
        完整验证许可证
        
        Args:
            license_file_path: 许可证文件路径
            
        Returns:
            (是否有效, LicenseInfo对象, 错误信息)
        """
        info = None
        try:
            # 解析许可证
            info = self.parse_license(license_file_path)
            if not info:
                return False, None, "许可证文件解析失败"
            
            # 验证签名
            print("\n=== 验证签名 ===")
            if not self.verify_signature(info):
                return False, info, "许可证签名验证失败"
            print("签名验证通过")
            
            # 验证硬件指纹
            print("\n=== 验证硬件指纹 ===")
            hw_valid, hw_msg = self.verify_hardware(info)
            if not hw_valid:
                return False, info, f"硬件指纹验证失败: {hw_msg}"
            
            # 验证有效期
            print("\n=== 验证有效期 ===")
            validity_valid, validity_msg = self.verify_validity(info)
            if not validity_valid:
                return False, info, f"有效期验证失败: {validity_msg}"
            
            return True, info, "许可证验证通过"
            
        finally:
            # 清理临时目录
            self.cleanup()


# 便捷函数
def validate_license(license_file_path: str, public_key_path: str = "../assets/public_key.pem") -> tuple[bool, Optional[LicenseInfo], str]:
    """
    验证许可证便捷函数
    
    Args:
        license_file_path: 许可证文件路径
        public_key_path: 公钥文件路径
        
    Returns:
        (是否有效, LicenseInfo对象, 错误信息)
    """
    validator = LicenseValidator(public_key_path)
    return validator.validate(license_file_path)


if __name__ == "__main__":
    # 测试
    import sys
    
    if len(sys.argv) > 1:
        license_path = sys.argv[1]
    else:
        license_path = "gwq-hardware051402.icr.lic"
    
    print("=" * 60)
    print("许可证验证测试")
    print("=" * 60)
    print(f"许可证文件: {license_path}")
    print()
    
    if os.path.exists(license_path):
        valid, info, msg = validate_license(license_path)
        print(f"\n验证结果: {'通过' if valid else '失败'}")
        print(f"消息: {msg}")
        if info:
            print(f"\n许可证信息:")
            print(f"  CPU ID: {info.cpu_id}")
            print(f"  MAC: {info.mac}")
            print(f"  磁盘序列号: {info.disk_serial}")
            print(f"  产品类型: {info.product_type}")
            print(f"  版本: {info.request_version}")
            print(f"  有效天数: {info.request_days}")
            print(f"  开始时间: {info.start_time}")
            print(f"  签名状态: {'有效' if info.verified else '未验证'}")
    else:
        print(f"许可证文件不存在: {license_path}")
