"""
数据协调器模块

负责管理与爱快路由器的数据交互。
通过异步子进程调用外部 'ikuai-cli' 工具获取系统状态、在线用户等信息。
采用 Home Assistant 的 DataUpdateCoordinator 模式实现数据刷新和实体同步。
"""
import asyncio
import json
import logging
import os
from typing import Optional

from homeassistant.exceptions import HomeAssistantError, UpdateFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import ENV_IKUAI_CLI_BASE_URL, ENV_IKUAI_CLI_TOKEN

_LOGGER = logging.getLogger(__name__)


class IkuaiDataCoordinator(DataUpdateCoordinator):
    """
    爱快路由器数据协调器
    
    负责：
    - 定期从路由器获取最新数据（CPU、内存、在线用户等）
    - 解析 CLI 工具返回的 JSON 数据
    - 通知注册的实体更新状态
    
    Attributes:
        config: 配置信息，包含 base_url, token, binary_path
    """

    def __init__(self, hass, config_entry):
        """
        初始化数据协调器
        
        Args:
            hass: Home Assistant 实例
            config_entry: 配置入口对象，包含用户配置的路由器 IP、Token、CLI路径等
        
        Sets up the coordinator with a 30-second update interval.
        """
        super().__init__(
            hass,
            name="ikuai_router",           # 协调器的唯一名称
            update_interval=30,             # 每30秒自动刷新一次数据
            update_method=self._async_update_data,  # 指定数据更新方法
        )
        self.config = config_entry.data  # 保存配置信息供后续使用

    async def _run_cli_command(self, command: str) -> dict:
        """
        执行 ikuai-cli 命令并返回解析后的 JSON 数据
        
        Args:
            command: 要执行的 CLI 命令字符串（如 'monitor system --format json'）
        
        Returns:
            dict: 解析后的 JSON 数据字典
            
        Raises:
            UpdateFailed: 如果命令执行失败或返回无效 JSON
        
        This method handles subprocess creation, environment variable setup,
        and JSON parsing for CLI commands.
        """
        # 构建完整的命令列表：[cli_path, ...args]
        full_cmd = [self.config.get("binary_path", "/usr/local/bin/ikuai-cli")] + command.split()

        # 复制当前环境变量并添加爱快专用的配置变量
        env = os.environ.copy()
        env[ENV_IKUAI_CLI_BASE_URL] = self.config["base_url"]    # 路由器地址
        env[ENV_IKUAI_CLI_TOKEN] = self.config.get("token", "")  # API Token

        # 异步创建子进程执行命令
        process = await asyncio.create_subprocess_exec(
            *full_cmd,                          # 展开命令参数
            stdout=asyncio.subprocess.PIPE,     # 捕获标准输出
            stderr=asyncio.subprocess.PIPE,     # 捕获错误输出
            env=env                             # 设置环境变量
        )

        # 等待进程完成并获取输出
        stdout, stderr = await process.communicate()

        # 检查命令是否成功执行
        if process.returncode != 0:
            _LOGGER.error(f"CLI命令执行失败: {stderr.decode()}")
            raise UpdateFailed("命令执行错误")

        # 尝试解析 JSON 输出
        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            # 如果返回的不是有效 JSON，抛出异常
            raise UpdateFailed("CLI 返回无效的 JSON 数据")

    async def _async_update_data(self):
        """
        从爱快路由器获取最新数据的异步方法
        
        Returns:
            dict: 包含系统信息和在线用户列表的数据字典
        
        This method is called periodically by the coordinator.
        It fetches system status and online users, handling errors gracefully.
        """
        # 1. 获取系统信息（CPU、内存、运行时间、WAN IP）
        try:
            system = await self._run_cli_command("monitor system --format json")
            sys_data = system.get("data", {})  # 提取 'data' 字段
        except Exception as e:
            _LOGGER.warning(f"获取系统信息失败: {e}")
            sys_data = {}  # 如果失败，返回空字典

        # 2. 获取在线用户列表
        online_users = []
        try:
            users_resp = await self._run_cli_command("users online --format json")
            raw_users = users_resp.get("data", [])  # 提取 'data' 字段（可能是列表）
            
            # 遍历每个用户，提取关键字段
            for u in raw_users:
                if isinstance(u, dict):  # 确保是字典类型
                    online_users.append({
                        "id": u.get("id"),           # 用户 ID（用于踢人操作）
                        "ip": u.get("ip_addr"),      # IP 地址
                        "mac": u.get("mac_addr"),    # MAC 地址
                        "name": u.get("username", "Unknown")  # 用户名，默认为 Unknown
                    })
        except Exception as e:
            _LOGGER.warning(f"获取在线用户失败: {e}")

        # 返回整合后的数据
        return {
            "system": sys_data,           # 系统状态信息
            "online_users": online_users, # 在线用户列表
            "online_count": len(online_users)  # 在线用户数量
        }