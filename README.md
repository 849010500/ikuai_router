# iKuai Router Integration for Home Assistant

<div align="center">

<a href="https://github.com/ikuaidev/homeassistant-ikuai-router/releases"><img src="https://img.shields.io/github/v/release/ikuaidev/homeassistant-ikuai-router" alt="GitHub release"></a>
<img src="https://img.shields.io/badge/Home_Assistant_2023.1+-blue?logo=home-assistant" alt="Home Assistant">

</div>

一个用于 Home Assistant 的自定义组件，通过调用本地 `ikuai-cli` 工具来实时监控和管理 iKuai (爱快) 路由器。

## ✨ 功能特性

*   **📊 系统监控**：实时查看 CPU 使用率、内存使用率、运行时间以及 WAN 口公网 IP。
*   **📡 设备追踪**：自动发现并追踪所有连接在爱快路由器上的有线/无线设备（手机、电脑等）。
*   **🚫 访客管理**：一键踢人功能，可以快速将违规或不需要网络访问的设备从路由器断开。
*   **🛡️ 状态监控**：监控路由器的防火墙状态及在线用户数量。

## 📋 前置条件

在安装此插件之前，请确保您的 Home Assistant 运行环境满足以下要求：

1.  **iKuai Router**：拥有一台爱快软路由或硬件路由器，且 API 功能已启用。
2.  **ikuai-cli 工具**：组件依赖外部的 Go 语言编写的 CLI 工具 (`ikuai-cli`)。
    *   您需要在运行 Home Assistant 的系统上安装该二进制文件（默认为 `/usr/local/bin/ikuai-cli`）。
3.  **API Token**：从爱快路由器的 Web 界面获取 API Token。

> **如何获取 Token？**
> 登录爱快后台 -> 系统管理 -> 用户设置 -> 开启 RESTful API，并复制生成的 Token。

## 📥 安装指南

### 第一步：安装 ikuai-cli

确保 Home Assistant 所在的 Linux/Docker 环境中安装了 `ikuai-cli`。

```bash
# 示例：将二进制文件复制到系统路径（请根据您的实际环境调整）
curl -fsSL https://github.com/ikuaidev/ikuai-cli/releases/download/v0.1.0/ikuai-cli_linux_amd64.tar.gz | tar -xzf -
sudo mv ikuai-cli /usr/local/bin/
chmod +x /usr/local/bin/ikuai-cli
```

### 第二步：安装 Home Assistant 插件

将本仓库的 `custom_components/ikuai_router` 文件夹复制到您的 Home Assistant 配置目录中。

**如果您使用的是 Docker：**
```bash
docker cp ikuai_router <your-ha-container>:/config/custom_components/
```

**如果您使用的是 Home Assistant OS / Supervised：**
```bash
mkdir -p /usr/share/hassio/homeassistant/custom_components
cp -r custom_components/ikuai_router /usr/share/hassio/homeassistant/custom_components/
```

## ⚙️ 配置方法

1.  重启 Home Assistant。
2.  进入 **设置** -> **设备与服务**。
3.  点击右下角的 **“添加集成”**。
4.  搜索并选择 **"iKuai Router"**。
5.  在弹出的配置窗口中填写：
    *   **IP Address (base_url)**: 爱快路由器的管理 IP（例如 `http://192.168.1.1`）。
    *   **Token**: 您在爱快后台生成的 API Token。
    *   **CLI Path (可选)**: 如果 CLI 工具不在默认路径，请指定完整路径。

## 📱 支持的实体

配置成功后，您将在 Home Assistant 中看到以下新设备：

### 1. iKuai Router System (传感器)
*   **CPU 使用率** (`sensor.i_kuai_router_cpu_usage`) - 显示百分比 %
*   **内存使用率** (`sensor.i_kuai_router_memory_usage`) - 显示百分比 %
*   **运行时间** (`sensor.i_kuai_router_uptime`) - 显示系统运行时长
*   **WAN IP** (`sensor.i_kuai_router_wan_ip`) - 当前公网 IPv4/IPv6 地址

### 2. Connected Devices (设备追踪器)
*   自动为每个在线用户生成一个 `device_tracker` 实体。
*   包含属性：`ip_address`, `mac_address`, `friendly_name`。
*   可用于自动化触发（例如：检测到特定手机连接后打开空调）。

### 3. Kick Switches (开关)
*   为每个在线用户生成一个“踢人”开关 (`switch.kick_user`)。
*   **用法**：点击开关即可将该设备从网络断开。状态会自动刷新。

## 🛠️ 开发与贡献

如果您想修改代码或添加新功能：

```bash
# 克隆仓库
git clone https://github.com/ikuaidev/homeassistant-ikuai-router.git
cd homeassistant-ikuai-router

# 运行测试 (需要 Python 环境)
pip install -r requirements.txt
pytest tests/
```

## 📜 许可

本项目基于 MIT 许可证开源。详见 [LICENSE](./LICENSE)。

---
*Powered by [iKuai Router](https://www.koolan.com/) & [ikuai-cli](https://github.com/ikuaidev/ikuai-cli)*