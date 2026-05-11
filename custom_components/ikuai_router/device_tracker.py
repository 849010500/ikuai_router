"""
设备追踪器实体模块

用于监控和追踪连接到爱快路由器的在线设备。
每个在线用户都会被创建一个独立的设备追踪器实体，支持以下功能：
- 实时显示设备IP地址
- 实时显示设备MAC地址
- 检测设备的连接状态（在线/离线）
"""
import logging
from homeassistant.components.device_tracker import DeviceScannerEntity, Entity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class IkuaiDevice(Entity):
    """
    爱快路由器在线设备追踪器实体

    每个连接到路由器的用户/设备都会创建一个这样的实体。
    它跟踪设备的IP地址、MAC地址和连接状态。

    Attributes:
        coordinator: 数据协调器，提供最新的在线用户列表
        ip_address: 设备的IP地址（字符串）
        mac: 设备的MAC地址（字符串）
        _name: 设备名称或用户名
        entry_id: Home Assistant配置入口的唯一ID
    """

    def __init__(self, coordinator, ip_address: str, mac: str, name: str, entry_id: str):
        """
        初始化设备追踪器实体

        Args:
            coordinator: IkuaiDataCoordinator 实例，负责提供在线用户数据
            ip_address: 设备的IP地址，如 '192.168.1.100'
            mac: 设备的MAC地址，如 'AA:BB:CC:DD:EE:FF'。如果为空则使用IP作为唯一标识
            name: 设备名称或用户名，用于显示。默认为 "Unknown Device"
            entry_id: Home Assistant配置入口的唯一ID，用于生成实体的全局唯一标识符
        """
        self.coordinator = coordinator
        self.ip_address = ip_address      # 保存IP地址供后续使用
        self.mac = mac                    # 保存MAC地址供后续使用
        self._name = name                 # 设备/用户名称
        self.entry_id = entry_id          # 配置入口ID，用于生成唯一标识符

    @property
    def name(self) -> str:
        """
        返回设备的显示名称

        Returns:
            str: 格式为 "{设备名} ({IP地址})" 的完整名称
        """
        return f"{self._name} ({self.ip_address})"  # 显示格式：设备名 + IP地址

    @property
    def unique_id(self) -> str:
        """
        返回设备的唯一标识符

        Returns:
            str: 全局唯一的设备ID。优先使用MAC地址，如果没有则使用IP地址

        Format:
            - 有MAC地址: "{entry_id}_{mac}"
            - 无MAC地址: "{entry_id}_{ip_address}"
        """
        # 优先使用MAC地址作为唯一标识，如果没有则使用IP地址
        return f"{self.entry_id}_{self.mac}" if self.mac else f"{self.entry_id}_{self.ip_address}"

    @property
    def ip_address(self) -> str:
        """
        返回设备的IP地址（此属性必须存在，因为 DeviceScannerEntity 需要它）

        Returns:
            str: 设备的IPv4或IPv6地址字符串
        """
        return self.ip_address  # 直接返回保存的IP地址

    @property
    def mac_address(self) -> str:
        """
        返回设备的MAC地址

        Returns:
            str: 设备的MAC地址字符串，如果没有则返回空字符串
        """
        return self.mac  # 直接返回保存的MAC地址

    @property
    def device_info(self):
        """
        返回设备信息，将在线设备关联到爱快路由器这个物理设备

        Returns:
            DeviceInfo: 包含制造商、型号等元数据的对象
        """
        return DeviceInfo(
            identifiers={(DOMAIN, self.unique_id)},  # 唯一标识符：(域名, 设备ID)
            name=self._name,                         # 设备名称
            via_device=(DOMAIN, f"{self.entry_id}_router"),  # 关联到路由器父设备
        )

    @property
    def should_poll(self) -> bool:
        """
        返回是否应该启用轮询

        Returns:
            bool: False，因为数据更新由协调器驱动，不需要额外轮询
        """
        return False  # 不使用轮询，由协调器自动触发更新

    async def async_added_to_hass(self):
        """
        当实体添加到 Home Assistant 时调用

        This method registers a listener so that the device tracker
        will automatically update its state when the coordinator's data changes.
        It ensures real-time tracking of connection status (online/offline).
        """
        # 注册一个监听器，当协调器的数据更新时自动调用 _handle_update 方法
        self.async_on_remove(
            self.coordinator.async_add_listener(self._handle_update)
        )

    @property
    def is_connected(self) -> bool:
        """
        检查设备当前是否在线（已连接）

        Returns:
            bool: True 表示设备当前在线，False 表示离线或不存在
        """
        # 从协调器数据中获取最新的在线用户列表
        users = self.coordinator.data.get("online_users", [])

        # 遍历每个在线用户，尝试匹配当前设备
        for user in users:
            # 优先使用MAC地址匹配（更准确），如果没有MAC则使用IP地址匹配
            if (self.mac and user.get("mac") == self.mac) or \
               user.get("ip") == self.ip_address:
                return True  # 找到匹配，说明设备在线

        return False  # 没有找到匹配，说明设备离线

    def _handle_update(self):
        """
        处理来自协调器的数据更新通知

        This method is called automatically when the coordinator's data changes.
        It triggers an update of this entity's state in Home Assistant.
        """
        # 标记实体状态需要更新，并立即刷新到前端显示
        self.async_schedule_update_ha_state(True)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """
    从配置入口设置设备追踪器实体

    This function is called by Home Assistant when setting up the integration.
    It creates a device tracker entity for each currently online user/device.

    Args:
        hass: Home Assistant 实例，用于管理实体注册
        config_entry: 配置入口对象，包含用户配置信息
        async_add_entities: 异步添加实体的回调函数

    This function creates device tracker entities for all currently connected devices.
    If a user is offline, no entity is created for them until they reconnect.
    """
    # 从 hass.data 中获取已创建的协调器实例
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]

    # 定义一个空列表，用于存储要创建的设备追踪器实体
    devices = []

    # 检查协调器是否有有效的数据且包含在线用户列表
    if coordinator.data and "online_users" in coordinator.data:
        # 遍历每个在线用户，为它们创建设备追踪器实体
        for user_data in coordinator.data["online_users"]:
            # 创建 IkuaiDevice 实例
            dev = IkuaiDevice(
                coordinator,                              # 数据协调器
                user_data.get("ip", ""),                  # IP地址，默认为空字符串
                user_data.get("mac", ""),                 # MAC地址，默认为空字符串
                user_data.get("name", "Unknown Device"),  # 设备名称，默认为 "Unknown Device"
                config_entry.entry_id                     # 配置入口ID
            )
            devices.append(dev)  # 将创建的设备添加到列表中

    # 将所有设备追踪器实体添加到 Home Assistant
    async_add_entities(devices)