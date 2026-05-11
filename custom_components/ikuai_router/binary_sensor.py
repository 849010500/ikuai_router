"""
爱快路由器二进制传感器模块

提供状态类监控实体，例如防火墙状态、WAN 连接状态等。
这些传感器通常只有两种状态：开启 (on) / 关闭 (off)。
"""
import logging
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class IkuaiFirewallStatus(BinarySensorEntity):
    """
    爱快路由器防火墙状态传感器

    监控防火墙是否处于开启状态。
    """

    def __init__(self, coordinator, config_entry):
        """
        初始化防火墙状态传感器

        Args:
            coordinator: 数据协调器实例，用于获取系统配置数据
            config_entry: 配置条目对象
        """
        self.coordinator = coordinator      # 存储协调器引用以获取数据
        self.config_entry = config_entry    # 存储配置条目引用
        self._attr_name = "防火墙状态"       # 设置传感器名称为中文

    @property
    def unique_id(self) -> str:
        """
        返回传感器的唯一标识符

        Returns:
            str: 格式化为 "{entry_id}_firewall_status" 的唯一 ID
        """
        return f"{self.config_entry.entry_id}_firewall_status"

    @property
    def device_info(self):
        """
        返回设备信息，将此传感器关联到爱快路由器这个物理设备

        Returns:
            DeviceInfo: 包含制造商、型号等元数据的对象
        """
        return DeviceInfo(
            identifiers={(DOMAIN, self.config_entry.entry_id)},
            name="爱快路由器",
            manufacturer="爱快",
            model="Router",
        )

    @property
    def is_on(self) -> bool:
        """
        返回防火墙是否开启

        Returns:
            bool: True 表示防火墙已启用，False 表示禁用。如果无法确定则默认为 True（安全策略）。
        """
        try:
            # 从协调器数据中提取系统配置中的防火墙状态
            sys_data = self.coordinator.data.get("system", {})
            return sys_data.get("firewall_enabled", True)
        except (KeyError, TypeError):
            return True  # 默认开启，确保安全性

    @property
    def should_poll(self) -> bool:
        """
        返回是否需要主动轮询

        Returns:
            bool: False（不使用轮询模式）
        """
        return False

    async def async_added_to_hass(self):
        """
        当实体被添加到 Home Assistant 时调用

        注册一个监听器，当协调器数据更新时自动触发此实体的状态刷新。
        """
        self.async_on_remove(
            self.coordinator.async_add_listener(self._handle_update)
        )

    def _handle_update(self):
        """
        处理来自协调器的数据更新事件

        当协调器刷新数据后，自动调用此方法并请求 Home Assistant 更新 UI 显示状态。
        """
        self.async_schedule_update_ha_state(True)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """
    从配置条目设置 iKuai 二进制传感器

    此函数由 Home Assistant 调用，负责创建所有二进制传感器实体并添加到 HA 中。
    目前仅包含防火墙状态监控。

    Args:
        hass: Home Assistant 实例
        config_entry: 当前配置条目对象
        async_add_entities: 添加实体的回调函数
    """
    # 从 hass.data 获取协调器
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]

    # 创建二进制传感器列表：目前仅包含防火墙状态
    binary_sensors = [
        IkuaiFirewallStatus(coordinator, config_entry),
    ]

    # 将所有创建的实体添加到 Home Assistant
    async_add_entities(binary_sensors)