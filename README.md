# iKuai Router Integration for Home Assistant

<div align="center">

<a href="https://github.com/8490500/ikuai_router/releases"><img src="https://img.shields.io/github/v/release/8490500/ikuai_router" alt="GitHub release"></a>
<img src="https://img.shields.io/badge/Home_Assistant_2023.1+-blue?logo=home-assistant" alt="Home Assistant">

</div>

一个用于 Home Assistant 的自定义组件，通过 `ikuai-cli` 工具来实时监控和管理 iKuai (爱快) 路由器。

## ✨ 功能特性

*   **📊 系统监控**：实时查看 CPU 使用率、内存使用率、运行时间以及 WAN 口公网 IP。
*   **📡 设备追踪**：自动发现并追踪所有连接在爱快路由器上的有线/无线设备（手机、电脑等）。
*   **🚫 访客管理**：一键踢人功能，可以快速将违规或不需要网络访问的设备从路由器断开。
*   **🛡️ 状态监控**：监控路由器的在线状态及在线用户数量。

## 📋 前置条件

在安装此插件之前，请确保您的 Home Assistant 运行环境满足以下要求：

1.  **iKuai Router**：拥有一台爱快软路由或硬件路由器，且 API 功能已启用。
2.  **API Token**：从爱快路由器的 Web 界面获取 API Token。

> **如何获取 Token？**
> 登录爱快后台 -> 系统管理 -> 用户设置 -> 开启 RESTful API，并复制生成的 Token。

## 📥 安装指南

### 方法一：HACS 安装（推荐）

1.  确保您已安装 [HACS](https://hacs.xyz/)。
2.  在 HACS 中添加自定义存储库：`https://github.com/8490500/ikuai_router`。
3.  搜索 "iKuai Router" 并安装。
4.  重启 Home Assistant。

### 方法二：手动安装

1.  下载最新版本的代码（或克隆仓库）。
2.  将 `custom_components/ikuai_router` 文件夹复制到 Home Assistant 的 `config/custom_components/` 目录。
3.  重启 Home Assistant。

## ⚙️ 配置

在 Home Assistant 中添加集成：

1.  进入 **设置** -> **设备与服务** -> **添加集成**。
2.  搜索 **"Ikuai Router"**。
3.  填写以下信息：
    *   **Router URL**：爱快路由器的 Web 界面地址（例如：`http://192.168.1.1`）。
    *   **API Token**：从爱快后台获取的 API Token。
    *   **ikuai-cli path**（可选）：如果 `ikuai-cli` 已安装且不在系统 PATH 中，可指定其路径；否则插件会自动下载。

## 📊 可用传感器

| 传感器名称 | 设备类 | 单位 | 描述 |
|------------|--------|------|------|
| iKuai CPU 使用率 | - | % | 路由器 CPU 平均使用率 |
| iKuai CPU 温度 | temperature | °C | 路由器 CPU 温度 |
| iKuai 内存使用率 | - | % | 路由器内存使用百分比 |
| iKuai 运行时间 | - | - | 路由器连续运行时间 |
| iKuai 上传速度 | - | KB/s | 当前上传速率 |
| iKuai 下载速度 | - | KB/s | 当前下载速率 |
| iKuai 总上传流量 | - | GB | 累计上传数据量 |
| iKuai 总下载流量 | - | GB | 累计下载数据量 |
| iKuai 连接数 | - | - | TCP/UDP/ICMP 总连接数 |
| iKuai WAN IP | - | - | 路由器公网 IPv4 地址 |
| iKuai WAN IPv6 | - | - | 路由器公网 IPv6 地址 |
| iKuai 在线终端数 | - | devices | 当前连接的终端设备数量 |
| iKuai AP 在线数 | - | devices | 在线 AP 接入点数量 |
| iKuai 主机名 | - | - | 路由器主机名 |
| iKuai 固件版本 | - | - | 爱快固件版本信息 |

> **注意**：部分传感器包含 `extra_state_attributes` 属性，可在实体详情页查看详细信息。

## 📱 设备追踪器

插件会自动发现并追踪所有在线设备：

- **有线设备**：通过网线连接的路由器设备
- **无线设备**：通过 2.4G/5G WiFi 连接的设备
- **AP 设备**：通过接入点连接的设备

每个追踪器实体包含 IP 地址和 MAC 地址作为唯一标识。

## 🔌 开关（踢人功能）

为每个在线设备生成一个开关实体，名称格式为 `Kick <设备名称>`：

- **开启开关**：将设备踢出网络
- **关闭开关**：设备保持在线状态

> **警告**：使用踢人功能前请确认目标设备，避免意外断开重要设备。

## 🔧 二进制传感器

- **iKuai Router Status**：监控路由器在线状态
    - `on`：路由器在线且数据正常
    - `off`：路由器离线或数据异常
