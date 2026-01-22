# QuantumultX 配置生成器

这是一个用于生成 QuantumultX 个性化配置的脚本，专为青龙面板环境设计。脚本会自动从指定远程地址获取配置，与本地保存的配置副本比较，当检测到更新时，会合并个人配置并生成最终配置文件。

## 功能特点

- ✅ **智能更新检查**：比较远程配置与本地副本的MD5哈希，仅在配置有变化时才生成新配置
- ✅ **个人化配置**：通过环境变量添加个人MITM证书、策略组、重写规则等
- ✅ **青龙面板集成**：使用青龙内置通知系统，支持成功/失败通知
- ✅ **精简存储**：只保留最新生成的配置和远程配置副本，不保存历史备份
- ✅ **MITM证书修复**：自动修复MITM证书格式，确保配置文件正确
- ✅ **策略组智能添加**：将个人策略组添加到static部分的开始位置

## 文件结构

```
/ql/data/config/
├── QuantumultX.conf          # 最终生成的配置文件
├── qx_remote_backup.conf     # 远程配置副本（用于比较）
└── qx_remote_backup.conf.hash # 配置哈希文件

/ql/data/log/
└── quantumultx_generator.log # 脚本运行日志
```

## 快速开始

### 1. 安装依赖

确保青龙面板已安装 Python3，并安装必要的依赖：

```bash
pip3 install requests
```

### 2. 部署脚本

1. 在青龙面板中创建新脚本
2. 将脚本内容复制到脚本编辑器中
3. 保存脚本（例如命名为 `quantumultx_generator.py`）

### 3. 配置环境变量

在青龙面板的环境变量页面，添加以下环境变量：

#### 必需配置

```bash
# MITM证书配置（必须是纯字符串格式）
QX_MITM_PASSPHRASE=A24AB7DF
QX_MITM_P12=MIILuwIBAzCCC4UGCSqGSIb3DQEHAaCCC3YE...
```

#### 可选配置

```bash
# 远程配置地址（默认为 ddgksf2013 的配置）
QX_REMOTE_URL=https://ddgksf2013.top/Profile/QuantumultX.conf

# 本地配置文件路径
QX_CONFIG_PATH=/ql/data/config/QuantumultX.conf

# 日志文件路径
QX_LOG_FILE=/ql/data/log/quantumultx_generator.log

# 远程配置备份路径
QX_REMOTE_BACKUP=/ql/data/config/qx_remote_backup.conf
```

#### 个人化配置（可选）

```bash
# 重写规则（JSON数组格式）
QX_REWRITE_REMOTE=["https://github.com/ddgksf2013/Rewrite/raw/master/Function/EmbyPlugin.conf, tag=emby, update-interval=172800, opt-parser=false, enabled=true"]

# 服务器订阅
QX_SERVER_REMOTE=["https://example.com/subscribe, tag=我的订阅, update-interval=86400, enabled=true"]

# 策略组（JSON数组格式）
QX_POLICIES=["static=AiInOne,香港节点,美国节点,狮城节点, img-url=https://raw.githubusercontent.com/Orz-3/mini/master/Color/Global.png", "static=Steam,自动选择,台湾节点,direct,香港节点,日本节点,美国节点,狮城节点,proxy, img-url=https://raw.githubusercontent.com/Koolson/Qure/master/IconSet/Color/Steam.png"]

# DNS配置
QX_DNS=["server=223.5.5.5", "server=119.29.29.29"]

# 过滤器
QX_FILTER_REMOTE=["https://raw.githubusercontent.com/ddgksf2013/Filter/master/Unbreak.list, tag=节点选择, force-policy=你的策略组名, update-interval=86400, opt-parser=false, enabled=true"]

# 自定义section
QX_SECTION_CUSTOM="custom_key=custom_value\nanother_key=another_value"
```

### 4. 创建定时任务

在青龙面板的定时任务页面，添加新的定时任务：

- 命令：`task quantulumtx_generator.py`
- 定时规则：`0 8 * * *`（每天上午8点运行）
- 名称：QuantumultX配置生成

### 5. 首次运行

手动运行一次脚本以生成初始配置：

```bash
python3 /ql/data/scripts/quantumultx_generator.py
```

## 使用说明

### 运行方式

#### 1. 正常检查更新
```bash
python3 quantumultx_generator.py
```
- 检查远程配置是否有更新
- 有更新时：下载新配置、合并个人配置、生成最终配置
- 无更新时：跳过生成，不发送通知

#### 2. 强制更新
```bash
python3 quantumultx_generator.py --force
```
- 忽略检查结果，强制下载并生成新配置
- 总会发送通知（即使是相同的配置）

#### 3. 获取帮助
```bash
python3 quantumultx_generator.py --help
```

### 通知类型

脚本会在以下情况发送青龙通知：

1. **配置更新成功**（✅）：远程配置有更新并成功生成新配置
2. **强制更新成功**（🔧）：使用 `--force` 参数成功生成配置
3. **配置更新失败**（❌）：获取远程配置或生成配置失败

> **注意**：当远程配置无更新时，脚本不会发送任何通知，避免通知骚扰。

### MITM证书格式要求

MITM证书必须使用**纯字符串格式**，**不能**使用JSON数组格式：

```bash
# ✅ 正确格式（纯字符串）
QX_MITM_PASSPHRASE=A24AB7DF
QX_MITM_P12=MIILuwIBAzCCC4UGCSqGSIb3DQEHAaCCC3YE...

# ❌ 错误格式（JSON数组）
QX_MITM_PASSPHRASE=["A24AB7DF"]
QX_MITM_P12=["MIILuwIBAzCCC4UGCSqGSIb3DQEHAaCCC3YE..."]
```

### 策略组格式

策略组使用JSON数组格式，每个策略组必须是 `static=` 开头：

```json
[
  "static=策略组名称,服务器1,服务器2,服务器3, img-url=图标URL",
  "static=游戏加速,香港节点,日本节点,美国节点, img-url=https://example.com/game.png"
]
```

## 环境变量详解

### 基础配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `QX_REMOTE_URL` | 远程配置地址 | `https://ddgksf2013.top/Profile/QuantumultX.conf` |
| `QX_CONFIG_PATH` | 本地配置文件路径 | `/ql/data/config/QuantumultX.conf` |
| `QX_LOG_FILE` | 日志文件路径 | `/ql/data/log/quantumultx_generator.log` |
| `QX_REMOTE_BACKUP` | 远程配置备份路径 | `/ql/data/config/qx_remote_backup.conf` |

### MITM证书配置（必需）

| 变量名 | 说明 | 格式要求 |
|--------|------|----------|
| `QX_MITM_PASSPHRASE` | MITM证书密码 | 纯字符串 |
| `QX_MITM_P12` | MITM证书内容 | 纯字符串（base64编码的P12证书） |

### 个人化配置（可选）

| 变量名 | 说明 | 格式 |
|--------|------|------|
| `QX_REWRITE_REMOTE` | 远程重写规则 | JSON数组 |
| `QX_REWRITE_LOCAL` | 本地重写规则 | JSON数组 |
| `QX_SERVER_REMOTE` | 远程服务器订阅 | JSON数组 |
| `QX_POLICIES` | 策略组配置 | JSON数组 |
| `QX_DNS` | DNS配置 | JSON数组 |
| `QX_FILTER_REMOTE` | 远程过滤器 | JSON数组 |
| `QX_FILTER_LOCAL` | 本地过滤器 | JSON数组 |
| `QX_SECTION_*` | 自定义section | 字符串或JSON |
| `QX_REPLACE_*` | 全局替换规则 | JSON对象 |

## 示例配置

### 完整的环境变量示例

```bash
# 远程配置地址
QX_REMOTE_URL=https://ddgksf2013.top/Profile/QuantumultX.conf

# MITM证书（必需）
QX_MITM_PASSPHRASE=A24AB7DF
QX_MITM_P12=MIILuwIBAzCCC4UGCSqGSIb3DQEHAaCCC3YEgggqMIIDZTCCAk2gAwIBAgIIZmjaof...

# 个人策略组
QX_POLICIES=["static=AI服务,香港节点,美国节点,狮城节点, img-url=https://raw.githubusercontent.com/Orz-3/mini/master/Color/Global.png", "static=游戏加速,自动选择,台湾节点,direct,香港节点,日本节点,美国节点,狮城节点,proxy, img-url=https://raw.githubusercontent.com/Koolson/Qure/master/IconSet/Color/Steam.png"]

# 重写规则
QX_REWRITE_REMOTE=["https://github.com/ddgksf2013/Rewrite/raw/master/Function/EmbyPlugin.conf, tag=emby, update-interval=172800, opt-parser=false, enabled=true", "https://github.com/ddgksf2013/Rewrite/raw/master/AdBlock/Bilibili.conf, tag=BiliBili去广告, update-interval=172800, opt-parser=false, enabled=true"]

# 服务器订阅
QX_SERVER_REMOTE=["https://your-subscribe-url.com/link/your-token?mu=0, tag=我的订阅, update-interval=86400, enabled=true"]

# DNS配置
QX_DNS=["server=223.5.5.5", "server=119.29.29.29", "server=1.1.1.1"]
```

### 定时任务配置

在青龙面板定时任务页面，推荐设置：

- 任务名称：QuantumultX配置更新
- 命令：`task quantulumtx_generator.py`
- 定时规则：`0 8,20 * * *`（每天上午8点和晚上8点各检查一次）
- 是否启用：是

## 故障排除

### 常见问题

1. **MITM证书格式错误**
  - 错误信息：`passphrase格式错误，包含方括号`
  - 解决方法：确保MITM证书使用纯字符串格式，不要用JSON数组格式

2. **获取远程配置失败**
  - 错误信息：`获取远程配置失败`
  - 解决方法：检查网络连接，确认远程URL可访问

3. **配置生成失败**
  - 错误信息：`保存配置失败`
  - 解决方法：检查文件权限，确保青龙有写入权限

4. **通知未发送**
  - 可能原因：青龙通知模块路径不正确
  - 解决方法：检查青龙面板的通知配置，脚本会回退到控制台输出

### 日志查看

查看详细运行日志：
```bash
tail -f /ql/data/log/quantumultx_generator.log
```

### 手动测试

手动运行脚本并查看输出：
```bash
cd /ql/data/scripts
python3 quantumultx_generator.py --force
```

## 工作原理

1. **获取远程配置**：从指定URL下载QuantumultX配置
2. **检查更新**：计算配置的MD5哈希，与本地保存的副本比较
3. **生成配置**：如果配置有更新或使用 `--force` 参数：
  - 保存新的远程配置副本
  - 解析配置的各个section
  - 添加个人配置（MITM证书、策略组、重写规则等）
  - 验证MITM证书格式
  - 保存最终配置文件
4. **发送通知**：根据结果发送青龙通知

## 注意事项

1. **首次运行**：第一次运行时会自动下载远程配置并生成个性化配置
2. **证书安全**：MITM证书包含敏感信息，请妥善保管
3. **配置文件**：生成的 `QuantumultX.conf` 可以直接导入QuantumultX使用
4. **定时任务**：建议设置合理的检查频率，避免频繁请求远程服务器
5. **备份建议**：虽然脚本不保存历史备份，但建议定期手动备份重要配置

## 更新日志

### v1.0.0
- 初始版本发布
- 支持智能更新检查
- 支持个人化配置合并
- 集成青龙通知系统
- 修复MITM证书格式问题

## 技术支持

如遇到问题，请：
1. 查看日志文件：`/ql/data/log/quantumultx_generator.log`
2. 检查环境变量配置
3. 确保网络连接正常
4. 确认文件权限正确

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情