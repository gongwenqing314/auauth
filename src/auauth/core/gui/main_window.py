"""
主窗口模块
实现AuTool授权工具的PyQt6图形界面
"""
import os
import sys
import yaml
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QPlainTextEdit,
    QGroupBox, QGridLayout, QFileDialog, QMessageBox,
    QProgressBar, QSplitter, QFrame, QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon, QColor

from ..hardware import get_hardware_info, HardwareInfo
from ..license import LicenseValidator, LicenseInfo, validate_license
from ..gateway.auth_processor import execute_gateway_auth, AuthResult


class AuthWorker(QThread):
    """授权工作线程"""
    
    # 信号定义
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    result_signal = pyqtSignal(object)
    
    def __init__(self, gateway_address, gateway_port, admin_account, 
                 admin_password, license_info, local_ip=""):
        super().__init__()
        self.gateway_address = gateway_address
        self.gateway_port = gateway_port
        self.admin_account = admin_account
        self.admin_password = admin_password
        self.license_info = license_info
        self.local_ip = local_ip
        self.running = True
    
    def run(self):
        """执行授权流程"""
        try:
            self.log_signal.emit("开始执行网关授权流程...")
            self.progress_signal.emit(10)
            
            # 执行授权
            result = execute_gateway_auth(
                gateway_address=self.gateway_address,
                gateway_port=self.gateway_port,
                admin_account=self.admin_account,
                admin_password=self.admin_password,
                license_info=self.license_info,
                local_ip=self.local_ip
            )
            
            self.progress_signal.emit(100)
            self.result_signal.emit(result)
            
            if result.success:
                self.log_signal.emit(f"✓ 授权成功！")
                self.log_signal.emit(f"  访问用户: {result.access_user}")
                self.log_signal.emit(f"  访问密码: {result.access_password}")
            else:
                self.log_signal.emit(f"✗ 授权失败: {result.message}")
                
        except Exception as e:
            self.log_signal.emit(f"✗ 授权异常: {str(e)}")
            self.result_signal.emit(AuthResult(False, str(e)))
    
    def stop(self):
        """停止线程"""
        self.running = False
        self.wait(1000)


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self, config_path="config.yaml"):
        super().__init__()
        self.config = self._load_config(config_path)
        self.license_info: LicenseInfo = None
        self.hardware_info: HardwareInfo = get_hardware_info()
        self.auth_worker: AuthWorker = None
        
        self._init_ui()
        self._load_hardware_info()
    
    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        default_config = {
            "gateway": {
                "default_address": "192.168.1.1",
                "default_port": "23"
            },
            "gui": {
                "window_title": "AuTool 授权工具",
                "window_width": 900,
                "window_height": 700
            }
        }
        
        try:
            # 处理打包后的资源路径
            if hasattr(sys, '_MEIPASS'):
                # PyInstaller 打包后的路径
                base_path = sys._MEIPASS
                config_path = os.path.join(base_path, config_path)
            
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    if config:
                        return config
        except Exception as e:
            print(f"加载配置文件失败: {e}")
        
        return default_config
    
    def _init_ui(self):
        """初始化UI"""
        # 设置窗口属性
        gui_config = self.config.get("gui", {})
        self.setWindowTitle(gui_config.get("window_title", "AuTool 授权工具"))
        self.setMinimumSize(
            gui_config.get("window_width", 900),
            gui_config.get("window_height", 700)
        )
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # 创建各个区域
        main_layout.addWidget(self._create_input_group())
        main_layout.addWidget(self._create_button_group())
        main_layout.addWidget(self._create_info_group(), 1)
        main_layout.addWidget(self._create_log_group())
        
        # 状态栏
        self.statusBar().showMessage("就绪")
    
    def _create_input_group(self) -> QGroupBox:
        """创建输入区域"""
        group = QGroupBox("授权配置")
        layout = QGridLayout(group)
        layout.setSpacing(10)
        
        # 许可证文件
        layout.addWidget(QLabel("许可证文件:"), 0, 0)
        self.license_path_edit = QLineEdit()
        self.license_path_edit.setPlaceholderText("请选择许可证文件 (.lic)")
        layout.addWidget(self.license_path_edit, 0, 1)
        
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self._browse_license_file)
        layout.addWidget(browse_btn, 0, 2)
        
        # 网关地址
        layout.addWidget(QLabel("网关地址:"), 1, 0)
        self.gateway_address_edit = QLineEdit()
        gateway_config = self.config.get("gateway", {})
        self.gateway_address_edit.setText(
            gateway_config.get("default_address", "192.168.1.1")
        )
        layout.addWidget(self.gateway_address_edit, 1, 1)
        
        # 端口
        layout.addWidget(QLabel("端口:"), 1, 2)
        self.gateway_port_edit = QLineEdit()
        self.gateway_port_edit.setText(
            gateway_config.get("default_port", "23")
        )
        self.gateway_port_edit.setMaximumWidth(80)
        layout.addWidget(self.gateway_port_edit, 1, 3)
        
        # 管理员账号
        layout.addWidget(QLabel("管理员账号:"), 2, 0)
        self.admin_account_edit = QLineEdit()
        auth_config = self.config.get("auth", {})
        self.admin_account_edit.setText(
            auth_config.get("default_admin_account", "CMCCAdmin")
        )
        layout.addWidget(self.admin_account_edit, 2, 1, 1, 3)
        
        # 管理员密码
        layout.addWidget(QLabel("管理员密码:"), 3, 0)
        password_container = QWidget()
        password_layout = QHBoxLayout(password_container)
        password_layout.setContentsMargins(0, 0, 0, 0)
        password_layout.setSpacing(5)
        
        self.admin_password_edit = QLineEdit()
        self.admin_password_edit.setText(
            auth_config.get("default_admin_password", "aDm8H%MdA")
        )
        self.admin_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        password_layout.addWidget(self.admin_password_edit)
        
        self.toggle_password_btn = QPushButton("👁")
        self.toggle_password_btn.setMaximumWidth(30)
        self.toggle_password_btn.setMinimumWidth(30)
        self.toggle_password_btn.setCheckable(True)
        self.toggle_password_btn.clicked.connect(self._toggle_password_visibility)
        password_layout.addWidget(self.toggle_password_btn)
        
        password_layout.addStretch()
        password_layout.setStretch(0, 1)
        password_layout.setStretch(1, 0)
        
        layout.addWidget(password_container, 3, 1, 1, 3)
        
        # 本地IP（可选）
        layout.addWidget(QLabel("本地IP:"), 4, 0)
        self.local_ip_edit = QLineEdit()
        self.local_ip_edit.setPlaceholderText("可选，用于绑定本地地址")
        layout.addWidget(self.local_ip_edit, 4, 1, 1, 3)
        
        return group
    
    def _create_button_group(self) -> QGroupBox:
        """创建按钮区域"""
        group = QGroupBox("操作")
        layout = QHBoxLayout(group)
        layout.setSpacing(15)
        
        # 验证许可证按钮
        self.verify_btn = QPushButton("验证许可证")
        self.verify_btn.setMinimumHeight(35)
        self.verify_btn.clicked.connect(self._verify_license)
        layout.addWidget(self.verify_btn)
        
        # 导出硬件指纹按钮
        self.export_btn = QPushButton("导出硬件指纹")
        self.export_btn.setMinimumHeight(35)
        self.export_btn.clicked.connect(self._export_hardware)
        layout.addWidget(self.export_btn)
        
        # 开始授权按钮
        self.auth_btn = QPushButton("开始授权")
        self.auth_btn.setMinimumHeight(35)
        self.auth_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
            }
        """)
        self.auth_btn.clicked.connect(self._start_auth)
        layout.addWidget(self.auth_btn)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        return group
    
    def _create_info_group(self) -> QGroupBox:
        """创建信息显示区域"""
        group = QGroupBox("系统信息")
        layout = QVBoxLayout(group)
        
        # 使用分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 硬件信息
        hardware_widget = QWidget()
        hardware_layout = QVBoxLayout(hardware_widget)
        hardware_layout.setContentsMargins(5, 5, 5, 5)
        
        hardware_title = QLabel("<b>本机硬件信息</b>")
        hardware_layout.addWidget(hardware_title)
        
        self.hardware_text = QTextEdit()
        self.hardware_text.setReadOnly(True)
        self.hardware_text.setMaximumHeight(120)
        hardware_layout.addWidget(self.hardware_text)
        
        splitter.addWidget(hardware_widget)
        
        # 许可证信息
        license_widget = QWidget()
        license_layout = QVBoxLayout(license_widget)
        license_layout.setContentsMargins(5, 5, 5, 5)
        
        license_title = QLabel("<b>许可证信息</b>")
        license_layout.addWidget(license_title)
        
        self.license_text = QTextEdit()
        self.license_text.setReadOnly(True)
        self.license_text.setMaximumHeight(120)
        license_layout.addWidget(self.license_text)
        
        splitter.addWidget(license_widget)
        
        # 授权结果
        result_widget = QWidget()
        result_layout = QVBoxLayout(result_widget)
        result_layout.setContentsMargins(5, 5, 5, 5)
        
        result_title = QLabel("<b>授权结果</b>")
        result_layout.addWidget(result_title)
        
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMaximumHeight(120)
        result_layout.addWidget(self.result_text)
        
        splitter.addWidget(result_widget)
        
        # 设置分割器比例
        splitter.setSizes([300, 300, 300])
        
        layout.addWidget(splitter)
        
        return group
    
    def _create_log_group(self) -> QGroupBox:
        """创建日志区域"""
        group = QGroupBox("日志输出")
        layout = QVBoxLayout(group)
        
        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumBlockCount(1000)  # 限制最大行数
        layout.addWidget(self.log_text)
        
        # 清除日志按钮
        clear_btn = QPushButton("清除日志")
        clear_btn.clicked.connect(self._clear_log)
        layout.addWidget(clear_btn)
        
        return group
    
    def _load_hardware_info(self):
        """加载硬件信息"""
        hw = self.hardware_info
        info_text = f"""MAC地址: {hw.mac_address}
CPU ID: {hw.cpu_id}
磁盘序列号: {hw.disk_serial}
硬件指纹: {hw.get_hardware_fingerprint()}"""
        self.hardware_text.setText(info_text)
    
    def _browse_license_file(self):
        """浏览许可证文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择许可证文件",
            "",
            "License Files (*.lic);;All Files (*)"
        )
        if file_path:
            self.license_path_edit.setText(file_path)
            self._log(f"已选择许可证文件: {file_path}")
    
    def _toggle_password_visibility(self, checked: bool):
        """切换密码可见性"""
        if checked:
            self.admin_password_edit.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_password_btn.setText("🔒")
        else:
            self.admin_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_password_btn.setText("👁")
    
    def _verify_license(self):
        """验证许可证"""
        license_path = self.license_path_edit.text().strip()
        
        if not license_path:
            QMessageBox.warning(self, "警告", "请先选择许可证文件")
            return
        
        if not os.path.exists(license_path):
            QMessageBox.warning(self, "警告", f"许可证文件不存在: {license_path}")
            return
        
        self._log("开始验证许可证...")
        
        try:
            validator = LicenseValidator()
            valid, info, msg = validator.validate(license_path)
            
            self.license_info = info
            
            if valid and info:
                self._log(f"✓ 许可证验证通过: {msg}")
                self._update_license_info(info)
                QMessageBox.information(self, "验证成功", msg)
            else:
                self._log(f"✗ 许可证验证失败: {msg}")
                self._update_license_info(info)
                QMessageBox.warning(self, "验证失败", msg)
                
        except Exception as e:
            self._log(f"✗ 验证异常: {str(e)}")
            QMessageBox.critical(self, "错误", f"验证异常: {str(e)}")
    
    def _update_license_info(self, info: LicenseInfo):
        """更新许可证信息显示"""
        if not info:
            self.license_text.setText("未加载许可证")
            return
        
        status = "✓ 有效" if info.verified else "✗ 未验证"
        
        info_text = f"""产品类型: {info.product_type}
CPU ID: {info.cpu_id}
MAC: {info.mac}
磁盘序列号: {info.disk_serial}
版本: {info.request_version}
有效天数: {info.request_days}
开始时间: {info.start_time}
签名状态: {status}"""
        
        self.license_text.setText(info_text)
    
    def _export_hardware(self):
        """导出硬件指纹"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出硬件指纹",
            "hardware.pcfinger",
            "硬件指纹文件 (*.pcfinger);;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                if self.hardware_info.export_pcfinger(file_path):
                    self._log(f"✓ 硬件指纹已导出到: {file_path}")
                    QMessageBox.information(self, "导出成功", f"硬件指纹已导出到:\n{file_path}")
                else:
                    QMessageBox.warning(self, "导出失败", "导出硬件指纹失败")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出异常: {str(e)}")
    
    def _start_auth(self):
        """开始授权流程"""
        # 检查输入
        license_path = self.license_path_edit.text().strip()
        gateway_address = self.gateway_address_edit.text().strip()
        gateway_port = self.gateway_port_edit.text().strip()
        admin_account = self.admin_account_edit.text().strip()
        admin_password = self.admin_password_edit.text().strip()
        local_ip = self.local_ip_edit.text().strip()
        
        # 验证输入
        if not license_path:
            QMessageBox.warning(self, "警告", "请选择许可证文件")
            return
        
        if not os.path.exists(license_path):
            QMessageBox.warning(self, "警告", "许可证文件不存在")
            return
        
        if not gateway_address:
            QMessageBox.warning(self, "警告", "请输入网关地址")
            return
        
        if not admin_account:
            QMessageBox.warning(self, "警告", "请输入管理员账号")
            return
        
        if not admin_password:
            QMessageBox.warning(self, "警告", "请输入管理员密码")
            return
        
        # 如果许可证未验证，先验证
        if not self.license_info or not self.license_info.verified:
            self._log("许可证未验证，先进行验证...")
            self._verify_license()
            
            if not self.license_info or not self.license_info.verified:
                QMessageBox.warning(self, "警告", "许可证验证失败，无法继续授权")
                return
        
        # 禁用按钮
        self._set_buttons_enabled(False)
        
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # 清空结果
        self.result_text.clear()
        
        # 创建工作线程
        self.auth_worker = AuthWorker(
            gateway_address=gateway_address,
            gateway_port=gateway_port,
            admin_account=admin_account,
            admin_password=admin_password,
            license_info=self.license_info,
            local_ip=local_ip
        )
        
        # 连接信号
        self.auth_worker.log_signal.connect(self._log)
        self.auth_worker.progress_signal.connect(self._update_progress)
        self.auth_worker.result_signal.connect(self._handle_auth_result)
        self.auth_worker.finished.connect(self._on_auth_finished)
        
        # 启动线程
        self.auth_worker.start()
        
        self._log("=" * 50)
        self._log("开始网关授权流程...")
    
    def _set_buttons_enabled(self, enabled: bool):
        """设置按钮状态"""
        self.verify_btn.setEnabled(enabled)
        self.export_btn.setEnabled(enabled)
        self.auth_btn.setEnabled(enabled)
    
    def _update_progress(self, value: int):
        """更新进度条"""
        self.progress_bar.setValue(value)
    
    def _handle_auth_result(self, result: AuthResult):
        """处理授权结果"""
        if result.success:
            result_text = f"""授权状态: ✓ 成功
访问用户: {result.access_user}
访问密码: {result.access_password}
Telnet地址: {result.telnet_address}
Telnet端口: {result.telnet_port}"""
            self.result_text.setText(result_text)
            
            # 显示成功对话框
            QMessageBox.information(
                self,
                "授权成功",
                f"网关授权成功！\n\n"
                f"访问用户: {result.access_user}\n"
                f"访问密码: {result.access_password}\n"
                f"Telnet地址: {result.telnet_address}:{result.telnet_port}"
            )
        else:
            result_text = f"""授权状态: ✗ 失败
错误信息: {result.message}"""
            self.result_text.setText(result_text)
            
            QMessageBox.warning(self, "授权失败", result.message)
    
    def _on_auth_finished(self):
        """授权完成回调"""
        self._set_buttons_enabled(True)
        self.progress_bar.setVisible(False)
        self.statusBar().showMessage("授权流程完成")
    
    def _log(self, message: str):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.appendPlainText(f"[{timestamp}] {message}")
        
        # 滚动到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def _clear_log(self):
        """清除日志"""
        self.log_text.clear()
    
    def closeEvent(self, event):
        """关闭事件"""
        # 停止工作线程
        if self.auth_worker and self.auth_worker.isRunning():
            self.auth_worker.stop()
        
        event.accept()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle('Fusion')
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
