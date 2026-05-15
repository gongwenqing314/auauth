# AuAuth 安装指南

## 环境要求

- Python >= 3.8
- pip >= 21.0
- Git

## 快速安装

```bash
# 一行命令安装（推荐）
pip install git+https://github.com/gongwenqing314/AuTool.git git+https://github.com/gongwenqing314/auauth.git
```

## 详细安装步骤

### 步骤1：安装 AuTool 核心模块

AuAuth 依赖 AuTool 核心模块，需要先安装：

```bash
pip install git+https://github.com/gongwenqing314/AuTool.git
```

### 步骤2：安装 AuAuth

```bash
pip install git+https://github.com/gongwenqing314/auauth.git
```

### 步骤3：验证安装

```python
# 测试导入
from auauth import authorize_device, AuthClient, AuthConfig
from auauth.exceptions import AuAuthError, LicenseError

print("✓ AuAuth 安装成功!")
```

## 私有仓库访问

由于 AuTool 是私有仓库，安装时需要 GitHub 认证。

### 方式1：使用 Personal Access Token（推荐）

1. **生成Token**
   - 登录 GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
   - 点击 "Generate new token"
   - 勾选 `repo` 权限
   - 生成并保存 Token

2. **安装时使用Token**
   ```bash
   pip install git+https://<TOKEN>@github.com/gongwenqing314/AuTool.git
   pip install git+https://github.com/gongwenqing314/auauth.git
   ```

### 方式2：使用 SSH 密钥

1. **生成SSH密钥**
   ```bash
   ssh-keygen -t ed25519 -C "your_email@example.com"
   ```

2. **添加到GitHub**
   - 复制 `~/.ssh/id_ed25519.pub` 内容
   - GitHub → Settings → SSH and GPG keys → New SSH key

3. **使用SSH安装**
   ```bash
   pip install git+ssh://git@github.com/gongwenqing314/AuTool.git
   pip install git+ssh://git@github.com/gongwenqing314/auauth.git
   ```

### 方式3：配置Git凭证缓存

```bash
# 缓存凭证1小时
git config --global credential.helper 'cache --timeout=3600'

# 或永久存储（注意安全）
git config --global credential.helper store
```

## 开发模式安装

适用于需要修改代码的开发者：

```bash
# 克隆仓库
git clone https://github.com/gongwenqing314/AuTool.git
git clone https://github.com/gongwenqing314/auauth.git

# 开发模式安装（可编辑）
cd AuTool
pip install -e .

cd ../auauth
pip install -e .
```

## 从发布版本安装

如果仓库有发布版本（Release）：

```bash
# 下载特定版本
pip install git+https://github.com/gongwenqing314/auauth.git@v1.0.0
```

## 离线安装

适用于无网络环境：

### 步骤1：在有网络的机器上下载

```bash
# 下载wheel包
pip download -d ./packages auauth
pip download -d ./packages git+https://github.com/gongwenqing314/AuTool.git
```

### 步骤2：复制到目标机器安装

```bash
# 离线安装
pip install --no-index --find-links=./packages auauth
```

## 卸载

```bash
pip uninstall auauth
pip uninstall autool-auth  # 如果安装了AuTool
```

## 常见问题

### Q: 安装时提示 "Repository not found"

**原因**：没有访问私有仓库的权限

**解决**：
1. 确认已被添加为仓库协作者
2. 使用正确的认证方式（Token或SSH）

### Q: 安装时提示 "Command 'git' not found"

**原因**：未安装Git

**解决**：
```bash
# Windows: 下载安装 https://git-scm.com/download/win
# 或使用 winget
winget install Git.Git

# Linux
sudo apt install git  # Debian/Ubuntu
sudo yum install git  # CentOS/RHEL
```

### Q: pip install 报 SSL 错误

**原因**：网络代理或SSL证书问题

**解决**：
```bash
# 临时跳过SSL验证
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org git+https://github.com/gongwenqing314/auauth.git
```

### Q: Windows 上安装 gmssl 失败

**原因**：gmssl 可能需要编译工具

**解决**：
```bash
# 安装 Visual C++ Build Tools
# 或使用预编译 wheel
pip install --only-binary :all: gmssl
```

## 依赖说明

| 包名 | 版本 | 用途 |
|------|------|------|
| autool-auth | latest | 核心授权模块（来自AuTool） |
| gmssl | >=3.2.2 | SM2/SM3 国密算法 |
| pycryptodome | >=3.15.0 | AES 加密 |
| requests | >=2.28.0 | HTTP 请求 |
| psutil | >=5.9.0 | 硬件信息获取 |

## 更新

```bash
# 更新到最新版
pip install --upgrade git+https://github.com/gongwenqing314/auauth.git
```
