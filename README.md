# iKuai Router Integration for Home Assistant

<div align="center">

<a href="https://github.com/849010500/ikuai_router/releases"><img src="https://img.shields.io/github/v/release/849010500/ikuai_router" alt="GitHub release"></a>
<img src="https://img.shields.io/badge/Home_Assistant_2024.1+-blue?logo=home-assistant" alt="Home Assistant">
<img src="https://img.shields.io/badge/版本-0.1.54-green" alt="version">

</div>

一个用于 Home Assistant 的自定义组件，通过 `ikuai-cli` 工具实时监控 iKuai（爱快）路由器。

## ✨ 功能特性

*   **📊 系统监控**：CPU 使用率、CPU 温度、内存使用率、运行时间
*   **📈 网络状态**：实时上传/下载速度、累计流量、连接数（TCP/UDP/ICMP）
*   **🌐 接口信息**：WAN 口公网 IP（自动过滤内网 IP）、WAN IPv6
*   **📱 终端统计**：在线终端数（含 2.4G/5G/有线/无线分类）、AP 在线数
*   **🛡️ 状态监控**：路由器在线状态二进制传感器
*   **🔍 智能诊断**：端口自动探测、重新配置入口

## 📋 前置条件

1.  **iKuai Router**：一台爱快软路由或硬件路由器，且 RESTful API 功能已启用
2.  **API Token**：从爱快路由器 Web 界面获取 API Token

> **如何获取 Token？**
>
> 登录爱快后台 → **系统管理** → **用户设置** → 开启 **RESTful API**，复制生成的 Token。

> **注意**：集成通过 `ikuai-cli` 命令行工具访问路由器 API。如果未指定二进制路径，集成会自动下载适配当前系统架构的 `ikuai-cli`。

## 📥 安装指南

### 方法一：HACS 安装（推荐）

1.  确保您已安装 [HACS](https://hacs.xyz/)
2.  在 HACS 中添加自定义存储库：`https://github.com/849010500/ikuai_router`
3.  搜索 "iKuai Router" 并安装
4.  重启 Home Assistant

### 方法二：手动安装

1.  下载最新版本的代码（或克隆仓库）
2.  将 `custom_components/ikuai_router` 文件夹复制到 Home Assistant 的 `config/custom_components/` 目录
3.  重启 Home Assistant

## ⚙️ 配置

### 添加集成

1.  进入 **设置** → **设备与服务** → **添加集成**
2.  搜索 **"Ikuai Router"**
3.  填写以下信息：
    *   **Router URL**：爱快路由器的 Web 界面地址（例如 `http://192.168.1.1`）
    *   **API Token**：从爱快后台获取的 API Token
    *   **ikuai-cli path**（可选）：自定义 `ikuai-cli` 二进制路径；留空则自动下载

### 端口自动探测

如果填写的 URL **不包含端口**，集成会自动探测爱快常见 API 端口：

`8080`、`443`、`80`、`8443`、`9080`、`9090`、`88`、`8081`、`8000`

探测到可用端口后会自动填入 URL，只需确认即可。若探测失败，可手动填写**带正确端口**的完整地址（例如 `http://192.168.1.1:8080`）。

### 重新配置

已添加的集成支持直接修改连接信息：

**设备与服务** → iKuai Router → **配置** → 修改地址/Token/二进制路径

## 📊 传感器

| 传感器名称 | 设备类 | 单位 | 描述 |
|------------|--------|------|------|
| iKuai CPU 使用率 | - | % | CPU 平均使用率 |
| iKuai CPU 温度 | temperature | °C | CPU 温度 |
| iKuai 内存使用率 | - | % | 内存使用百分比 |
| iKuai 运行时间 | - | - | 连续运行时间 |
| iKuai 上传速度 | - | KB/s | 当前上传速率 |
| iKuai 下载速度 | - | KB/s | 当前下载速率 |
| iKuai 总上传流量 | - | GB | 累计上传数据量 |
| iKuai 总下载流量 | - | GB | 累计下载数据量 |
| iKuai 连接数 | - | - | TCP/UDP/ICMP 总连接数 |
| iKuai WAN IP | - | - | WAN 口公网 IP（自动过滤内网 IP） |
| iKuai WAN IPv6 | - | - | WAN 口 IPv6 地址（如可用） |
| iKuai 在线终端数 | - | devices | 当前连接终端数 |
| iKuai AP 在线数 | - | devices | 在线 AP 数量 |
| iKuai 主机名 | - | - | 路由器主机名 |
| iKuai 固件版本 | - | - | 爱快固件版本 |

> **提示**：部分传感器包含 `extra_state_attributes` 附加属性（如内存详情、连接详情、在线终端分类），可在实体详情页查看。

## 🔧 二进制传感器

| 传感器名称 | 描述 |
|------------|------|
| iKuai Router Status | 路由器在线状态<br>`on`：在线且数据正常<br>`off`：离线或数据异常 |

## 🔄 刷新机制

传感器数据通过 `DataUpdateCoordinator` 统一刷新，默认 **10 秒** 一次。

## 🛠️ 故障排查

### 所有传感器显示"未知"

1. 检查 Home Assistant 日志（**设置 → 系统 → 日志**）搜索 `ikuai_router`
2. 若出现 `连接失败: Get "http://...": dial tcp ... connection refused`：
   - 说明端口错误，请重新配置并**填写带正确端口的 URL**，或让集成自动探测
3. 若出现 `ikuai-cli binary not found`：
   - 检查自动下载是否成功，或手动指定 `ikuai-cli path`

### WAN IP 显示内网地址

- 集成已自动过滤内网 IP（`10.x`、`172.16-31.x`、`192.168.x`、`127.x`）
- 如果您的宽带本身分配的就是内网 IP（运营商 NAT 场景），WAN IP 显示内网是正常的

### 旧版本残留实体

v0.1.46 起移除了踢人开关和在线设备追踪功能。升级后旧实体由 `async_migrate_entry` 自动清理；如仍有残留，可在 **设置 → 设备与服务** 中手动删除。

## 📝 变更记录

请参阅 [CHANGELOG.md](CHANGELOG.md)。

## 📄 许可证

本项目基于 MIT 许可证开源。