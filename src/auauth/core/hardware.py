"""
硬件指纹获取模块
用于获取本机的MAC地址、CPU ID、磁盘序列号等硬件信息
"""
import re
import subprocess
import platform
import psutil
import hashlib
from typing import Optional, List


class HardwareInfo:
    """硬件信息类"""
    
    def __init__(self):
        self.mac_address: str = ""
        self.mac: str = ""  # mac_address的别名，兼容许可证字段名
        self.disk_serial: str = ""
        self.cpu_id: str = ""
        self._init_hardware_info()
    
    def _init_hardware_info(self):
        """初始化硬件信息"""
        self.mac_address = self._get_mac_address()
        self.mac = self.mac_address  # 保持一致
        self.disk_serial = self._get_disk_serial()
        self.cpu_id = self._get_cpu_id()
    
    def _get_mac_address(self) -> str:
        """
        获取本机MAC地址
        优先获取以太网适配器的MAC地址
        """
        try:
            # 获取所有网络接口
            interfaces = psutil.net_if_addrs()
            ethernet_macs = []
            
            for interface_name, addresses in interfaces.items():
                interface_name_lower = interface_name.lower()
                
                # 优先检测以太网/有线网络适配器
                is_ethernet = False
                
                if platform.system().lower() == "windows":
                    # Windows系统：判断是否为以太网适配器
                    is_ethernet = (
                        "ethernet" in interface_name_lower or
                        "以太网" in interface_name_lower or
                        interface_name_lower.startswith("eth") or
                        "realtek" in interface_name_lower or
                        "intel" in interface_name_lower
                    ) and not any(x in interface_name_lower for x in [
                        "wireless", "wi-fi", "wlan", "无线",
                        "vpn", "virtual", "bluetooth", "wifi"
                    ])
                else:
                    # Linux/Mac系统
                    is_ethernet = (
                        interface_name_lower.startswith("eth") or
                        interface_name_lower.startswith("en") or
                        "ethernet" in interface_name_lower
                    )
                
                # 获取MAC地址
                for addr in addresses:
                    if addr.family == psutil.AF_LINK:  # MAC地址
                        mac = addr.address.upper()
                        if mac and mac != "00-00-00-00-00-00" and mac != "FF-FF-FF-FF-FF-FF":
                            if is_ethernet:
                                # 如果是以太网适配器，优先返回
                                if not self._is_broadcast_mac(mac):
                                    return mac
                            ethernet_macs.append(mac)
            
            # 如果没有找到以太网MAC，返回第一个有效的MAC
            if ethernet_macs:
                return ethernet_macs[0]
            
            # 最后尝试：获取任意非虚拟接口的MAC
            for interface_name, addresses in interfaces.items():
                interface_name_lower = interface_name.lower()
                # 跳过虚拟适配器
                if any(x in interface_name_lower for x in [
                    "loopback", "virtual", "vmware", "virtualbox",
                    "hyper-v", "tunnel", "tap", "bluetooth"
                ]):
                    continue
                
                for addr in addresses:
                    if addr.family == psutil.AF_LINK:
                        mac = addr.address.upper()
                        if mac and not self._is_broadcast_mac(mac):
                            return mac
            
        except Exception as e:
            print(f"获取MAC地址时出错: {e}")
        
        return "获取失败"
    
    def _is_broadcast_mac(self, mac: str) -> bool:
        """检查是否为广播MAC地址"""
        clean_mac = mac.replace(":", "").replace("-", "").upper()
        return clean_mac in ["000000000000", "FFFFFFFFFFFF"]
    
    def _get_disk_serial(self) -> str:
        """
        获取磁盘序列号（Windows环境）
        """
        default_serial = "00A0_7501_3111_48A0"
        pattern = re.compile(r'[0-9A-Za-z]{4}_[0-9A-Za-z]{4}_[0-9A-Za-z]{4}_[0-9A-Za-z]{4}')
        
        try:
            if platform.system().lower() == "windows":
                # 方案1: 使用wmic命令
                try:
                    result = subprocess.run(
                        ["wmic", "diskdrive", "get", "serialnumber"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0:
                        lines = result.stdout.strip().split('\n')
                        for line in lines:
                            line = line.strip()
                            if line and line.lower() != "serialnumber":
                                match = pattern.search(line)
                                if match:
                                    return match.group()
                except Exception as e:
                    print(f"wmic获取磁盘序列号失败: {e}")
                
                # 方案2: 使用PowerShell
                try:
                    result = subprocess.run(
                        ["powershell", "-Command",
                         "Get-WmiObject Win32_PhysicalMedia | Select-Object SerialNumber"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0:
                        lines = result.stdout.strip().split('\n')
                        for line in lines:
                            line = line.strip()
                            if line and "serialnumber" not in line.lower() and "---" not in line:
                                serial = re.sub(r'\s+', '', line)
                                if serial:
                                    return serial
                except Exception as e:
                    print(f"PowerShell获取磁盘序列号失败: {e}")
            
            # 最终备用：生成基于系统信息的唯一标识
            return self._generate_fallback_id("disk")
            
        except Exception as e:
            print(f"获取磁盘序列号时出错: {e}")
        
        return default_serial
    
    def _get_cpu_id(self) -> str:
        """
        获取CPU ID
        """
        default_id = "00A0_7501_3111_48A0"
        
        try:
            if platform.system().lower() == "windows":
                # 方案1: 使用wmic命令
                try:
                    result = subprocess.run(
                        ["wmic", "cpu", "get", "processorid"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0:
                        lines = result.stdout.strip().split('\n')
                        for line in lines:
                            line = line.strip()
                            if line and line.lower() != "processorid":
                                cpu_id = re.sub(r'\s+', '', line)
                                if cpu_id:
                                    return self._format_cpu_id(cpu_id)
                except Exception as e:
                    print(f"wmic获取CPU ID失败: {e}")
                
                # 方案2: 使用PowerShell
                try:
                    result = subprocess.run(
                        ["powershell", "-Command",
                         "Get-WmiObject Win32_Processor | Select-Object ProcessorId"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0:
                        lines = result.stdout.strip().split('\n')
                        for line in lines:
                            line = line.strip()
                            if line and "processorid" not in line.lower() and "---" not in line:
                                cpu_id = re.sub(r'\s+', '', line)
                                if cpu_id:
                                    return self._format_cpu_id(cpu_id)
                except Exception as e:
                    print(f"PowerShell获取CPU ID失败: {e}")
            
            elif platform.system().lower() == "linux":
                # Linux系统：读取/proc/cpuinfo
                try:
                    result = subprocess.run(
                        ["grep", "-i", "serial", "/proc/cpuinfo"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        lines = result.stdout.strip().split('\n')
                        for line in lines:
                            if ":" in line:
                                cpu_id = line.split(":")[1].strip()
                                if cpu_id:
                                    return self._format_cpu_id(cpu_id)
                except Exception as e:
                    print(f"读取/proc/cpuinfo失败: {e}")
            
            # 最终备用：生成基于系统信息的唯一标识
            return self._generate_fallback_id("cpu")
            
        except Exception as e:
            print(f"获取CPU ID时出错: {e}")
        
        return default_id
    
    def _format_cpu_id(self, cpu_id: str) -> str:
        """格式化CPU ID，添加下划线"""
        if len(cpu_id) <= 4:
            return cpu_id
        
        formatted = []
        for i in range(0, len(cpu_id), 4):
            if i > 0:
                formatted.append("_")
            end = min(i + 4, len(cpu_id))
            formatted.append(cpu_id[i:end])
        
        return "".join(formatted)
    
    def _generate_fallback_id(self, id_type: str) -> str:
        """生成备用的唯一标识"""
        system_info = (
            platform.node() +  # 计算机名
            platform.machine() +  # 机器类型
            platform.processor() +  # 处理器信息
            id_type
        )
        hash_value = hashlib.md5(system_info.encode()).hexdigest().upper()
        # 格式化为 XXXX_XXXX_XXXX_XXXX 格式
        return f"{hash_value[:4]}_{hash_value[4:8]}_{hash_value[8:12]}_{hash_value[12:16]}"
    
    def get_hardware_fingerprint(self) -> str:
        """
        获取硬件指纹（用于网关授权）
        格式：MAC地址 + 设备类型
        """
        mac_clean = self.mac_address.replace(":", "").replace("-", "").upper()
        return f"{mac_clean}GATEWAY"
    
    def export_pcfinger(self, filepath: str) -> bool:
        """
        导出硬件指纹文件
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"MAC={self.mac_address}\n")
                f.write(f"DISK_SERIAL={self.disk_serial}\n")
                f.write(f"CPU_ID={self.cpu_id}\n")
                f.write("VERSION=V2026030301\n")
            return True
        except Exception as e:
            print(f"导出硬件指纹文件失败: {e}")
            return False
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "mac_address": self.mac_address,
            "disk_serial": self.disk_serial,
            "cpu_id": self.cpu_id,
            "hardware_fingerprint": self.get_hardware_fingerprint()
        }
    
    def __str__(self) -> str:
        return f"HardwareInfo(MAC={self.mac_address}, CPU={self.cpu_id}, Disk={self.disk_serial})"


# 全局硬件信息实例
_hardware_info: Optional[HardwareInfo] = None


def get_hardware_info() -> HardwareInfo:
    """获取硬件信息（单例模式）"""
    global _hardware_info
    if _hardware_info is None:
        _hardware_info = HardwareInfo()
    return _hardware_info


def refresh_hardware_info() -> HardwareInfo:
    """刷新硬件信息"""
    global _hardware_info
    _hardware_info = HardwareInfo()
    return _hardware_info


if __name__ == "__main__":
    # 测试
    hw = get_hardware_info()
    print(f"MAC地址: {hw.mac_address}")
    print(f"CPU ID: {hw.cpu_id}")
    print(f"磁盘序列号: {hw.disk_serial}")
    print(f"硬件指纹: {hw.get_hardware_fingerprint()}")
