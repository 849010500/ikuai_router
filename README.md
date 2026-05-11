# iKuai Router Integration for Home Assistant

<div align="center">

<a href="https://github.com/849010500/ikuai_router/releases"><img src="https://img.shields.io/github/v/release/849010500/ikuai_router" alt="GitHub release"></a>
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

git clone https://github.com/849010500/ikuai_router.git

