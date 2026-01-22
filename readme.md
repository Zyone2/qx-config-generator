# QuantumultX 配置生成器(AI)

基于 ddgksf2013 配置的个性化 QuantumultX 配置文件生成工具，专为青龙面板环境设计。

## 🌟 功能特性

- **自动化生成**：自动从 ddgksf2013 获取最新配置模板
- **个性化定制**：通过环境变量添加个人配置项
- **MITM 证书管理**：自动注入个人 MITM 证书配置
- **策略组智能添加**：将个人策略组添加到 static 部分开头
- **配置缓存**：支持 24 小时缓存，减少网络请求
- **自动备份**：每次生成自动备份新旧配置
- **去重机制**：避免重复添加相同配置项
- **全局替换**：支持配置内容的全局替换规则
- **日志记录**：详细的运行日志，便于问题排查

## 📁 文件结构

```
quantumultx-generator/
├── main.py              # 主脚本文件
├── subscribe.json       # 青龙面板订阅配置
├── requirements.txt     # Python 依赖包
└── README.md           # 说明文档
```

## ⚙️ 青龙面板配置

### 1. 添加订阅

在青龙面板中添加以下订阅：

```
https://raw.githubusercontent.com/[你的用户名]/[仓库名]/main/subscribe.json
```

### 2. 环境变量设置

在青龙面板的 `环境变量` 中添加以下变量（所有变量以 `QX_` 开头）：

#### MITM 证书配置（必需）
```bash
# MITM 证书密码（纯字符串格式）
QX_MITM_PASSPHRASE=你的证书密码

# MITM 证书内容（纯字符串格式，base64编码）
QX_MITM_P12=MIILuwIBAzCCC4UGCSqGSIb3DQEHAaCCC3YE...
```

#### 策略组配置（可选）
```bash
# 个人策略组（JSON数组格式）
QX_POLICIES=[
  "static=AiInOne,香港节点,美国节点,狮城节点,img-url=https://raw.githubusercontent.com/Orz-3/mini/master/Color/Global.png",
  "static=Steam,自动选择,台湾节点,direct,香港节点,日本节点,美国节点,狮城节点,proxy,img-url=https://raw.githubusercontent.com/Koolson/Qure/master/IconSet/Color/Steam.png"
]
```

#### 重写规则（可选）
```bash
# 远程重写规则（JSON数组格式）
QX_REWRITE_REMOTE=[
  "https://github.com/ddgksf2013/Rewrite/raw/master/Function/EmbyPlugin.conf, tag=emby, update-interval=172800, opt-parser=false, enabled=true",
  "https://github.com/ddgksf2013/Rewrite/raw/master/AdBlock/StartUp.conf, tag=去广告, update-interval=86400, opt-parser=true, enabled=true"
]
```

#### 服务器订阅（可选）
```bash
# 服务器订阅链接（JSON数组格式）
QX_SERVER_REMOTE=[
  "https://你的订阅链接, tag=我的订阅, update-interval=86400, enabled=true"
]
```

#### DNS 配置（可选）
```bash
# DNS 服务器配置
QX_DNS=[
  "server=114.114.114.114",
  "server=223.5.5.5",
  "server=119.29.29.29",
  "server=1.1.1.1"
]
```

#### 其他配置
```bash
# 远程配置地址（可自定义）
QX_REMOTE_URL=https://ddgksf2013.top/Profile/QuantumultX.conf

# 本地配置文件路径
QX_CONFIG_PATH=/ql/data/config/QuantumultX.conf

# 备份目录
QX_BACKUP_DIR=/ql/data/config/backup

# 日志文件路径
QX_LOG_FILE=/ql/data/log/quantumultx_generator.log

# 缓存文件路径
QX_CACHE_FILE=/ql/data/config/qx_config_cache.json
```

## 🔧 安装与使用

### 方法一：青龙面板订阅（推荐）

1. 在青龙面板中添加订阅链接
2. 配置环境变量
3. 脚本会自动定时运行

### 方法二：手动运行

```bash
# 克隆仓库
git clone https://github.com/你的用户名/ddgk2quanx.git
cd ddgk2quanx

# 安装依赖
pip install -r requirements.txt

# 设置环境变量（或在青龙面板中设置）
export QX_MITM_PASSPHRASE="你的密码"
export QX_MITM_P12="你的证书内容"

# 运行脚本
python main.py
```

## 📋 脚本工作原理

### 1. **配置获取阶段**
- 从远程获取 ddgksf2013 的最新配置
- 使用缓存机制减少网络请求
- 解析配置文件的各个 section

### 2. **个性化注入阶段**
- **MITM 证书**：替换或添加个人证书配置
- **策略组**：将个人策略组添加到 static 部分开头
- **重写规则**：去重后添加个人重写规则
- **服务器订阅**：添加个人服务器订阅链接
- **其他配置**：DNS、过滤器等个性化配置

### 3. **配置文件生成阶段**
- 按标准顺序重组配置 sections
- 应用全局替换规则
- 验证 MITM 证书格式
- 生成最终配置文件

### 4. **文件保存阶段**
- 备份原配置文件
- 保存新配置文件
- 记录详细日志

## 🚨 注意事项

### MITM 证书格式
**重要**：MITM 证书必须是纯字符串格式，不是 JSON 数组格式：

```bash
# ✅ 正确格式（纯字符串）
QX_MITM_PASSPHRASE=A24AB7DF
QX_MITM_P12=MIILuwIBAzCCC4UGCSqGSIb3DQE...

# ❌ 错误格式（JSON 数组）
QX_MITM_PASSPHRASE=["A24AB7DF"]
QX_MITM_P12=["MIILuwIBAzCCC4UGCSqGSIb3DQE..."]
```

### 策略组位置
- 个人策略组会自动添加到 `static=` 部分的**开头位置**
- 脚本会自动去重，避免重复添加相同的策略组

### 配置缓存
- 配置内容会缓存 24 小时
- 缓存文件位于：`/ql/data/config/qx_config_cache.json`
- 可通过环境变量 `QX_CACHE_FILE` 修改路径

### 备份机制
- 每次生成都会备份原配置文件和新配置文件
- 备份文件保存在：`/ql/data/config/backup/`
- 文件名包含时间戳：`QuantumultX_20240101_120000_old.conf`

## 🔍 故障排除

### 常见问题

1. **MITM 证书格式错误**
   ```
   错误信息：MITM证书信息不完整 或 passphrase格式错误，包含方括号
   解决方法：确保环境变量是纯字符串格式，不是JSON数组格式
   ```

2. **网络连接失败**
   ```
   错误信息：获取远程配置失败
   解决方法：检查网络连接，或修改QX_REMOTE_URL为可访问的地址
   ```

3. **权限问题**
   ```
   错误信息：Permission denied
   解决方法：检查青龙面板的文件权限，确保脚本有写入权限
   ```

4. **配置不生效**
   ```
   检查步骤：
   1. 查看日志文件：/ql/data/log/quantumultx_generator.log
   2. 检查环境变量是否设置正确
   3. 确认配置文件已保存到正确位置
   ```

### 日志查看

```bash
# 查看实时日志
tail -f /ql/data/log/quantumultx_generator.log

# 查看完整日志
cat /ql/data/log/quantumultx_generator.log
```

## 📊 生成统计

脚本运行后会显示以下统计信息：
- 原始配置大小
- 最终配置大小
- 配置变化量
- 已添加的个性化内容详情
- 个人策略组详情
- MITM 证书格式检查

## 🔄 更新说明

### v1.0 主要特性
- 基于 ddgksf2013 配置模板
- 支持环境变量个性化配置
- MITM 证书自动注入
- 策略组智能添加到开头
- 完整的备份和日志系统
- 青龙面板集成支持

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

- [ddgksf2013](https://github.com/ddgksf2013) - 提供 QuantumultX 配置模板
- QuantumultX 开发者 - 优秀的代理工具


## 📧 联系

如有问题或建议，请通过 GitHub Issues 联系。