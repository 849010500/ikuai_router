"""
爱快路由器 Home Assistant 自定义组件

这是一个用于集成爱快路由器的 Home Assistant 自定义组件。
它通过调用外部工具 'ikuai-cli' 来监控和管理爱快路由器。

支持的实体类型：
- 传感器（Sensor）：CPU使用率、内存使用率、运行时间、WAN IP等
- 设备追踪器（Device Tracker）：在线用户设备追踪
- 开关（Switch）：踢人功能
"""
import logging

from homeassistant.core import HomeAssistant
from .const import DOMAIN, CONFIG_ENTRY_TITLE
from .coordinator import IkuaiDataCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config):
    """
    设置爱快路由器组件
    
    Args:
        hass: Home Assistant 实例
        config: 配置文件
    
    Returns:
        bool: 始终返回 True，表示设置成功
    """
    # 目前我们主要通过配置入口（config entry）来配置，
    # 所以这个函数主要是做初始化准备
    return True


async def async_setup_entry(hass: HomeAssistant, entry) -> bool:
    """
    从配置入口设置爱快路由器
    
    Args:
        hass: Home Assistant 实例
        entry: 配置入口对象，包含用户配置的 IP、Token、CLI路径等信息
    
    Returns:
        bool: True 表示设置成功

    当集成从配置条目加载时调用此函数。
    它创建一个协调器来管理数据更新并设置所有实体平台。
    """
    # 创建数据协调器，负责定期从路由器获取最新数据
    coordinator = IkuaiDataCoordinator(hass, entry)
    
    # 首次刷新数据，确保组件启动时就有最新数据
    await coordinator.async_refresh()

    # 将协调器存储在 hass.data 中，以便其他实体可以访问
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
    }

    # 异步加载所有支持的实体平台（传感器、设备追踪器、开关等）
    await hass.config_entries.async_forward_entry_setup(entry, [
        "sensor",           # 系统状态传感器
        "device_tracker",   # 在线用户设备追踪
        "switch",           # 踢人控制开关
        "binary_sensor"     # 防火墙状态等二进制传感器
    ])

    return True


async def async_unload_entry(hass: HomeAssistant, entry) -> bool:
    """
    卸载配置入口及其所有实体
    
    Args:
        hass: Home Assistant 实例
        entry: 要卸载的配置入口
    
    Returns:
        bool: True 表示所有实体都成功卸载

    当用户移除或禁用集成时调用此函数。
    它卸载所有关联的实体并清理资源。
    """
    # 从 hass.data 中获取协调器引用（虽然这里没有实际使用，但保留引用）
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    
    # 异步卸载所有实体平台
    unload_ok = await hass.config_entries.async_forward_entry_unload(entry, [
        "sensor",
        "device_tracker", 
        "switch",
        "binary_sensor"
    ])

    # 如果所有实体都成功卸载，则从 hass.data 中移除该配置的协调器
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok"""
