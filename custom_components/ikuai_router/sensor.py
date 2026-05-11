"""
传感器实体模块

定义各种系统状态传感器，用于监控爱快路由器的关键指标。
支持的传感器类型：
- CPU使用率（百分比）
- 内存使用率（百分比）
- 运行时间（字符串格式）
- WAN IP地址
- 在线用户数量
"""
import logging
from homeassistant.helpers.entity import Entity, DeviceInfo
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class IkuaiSensor(Entity):
    """
    爱快路由器传感器的基类
    
    提供所有传感器共享的功能和属性：
    - 统一的命名规范（"iKuai Router <名称>"）
    - 设备信息关联
    - 可用性检查
    - 禁用轮询（由协调器驱动更新）
    
    Attributes:
        coordinator: 数据协调器实例，提供最新数据
        config_entry: 配置入口对象，用于生成唯一ID
        _name: 传感器显示名称的后缀部分
        _unique_id_suffix: 唯一标识符后缀
    """

    def __init__(self, coordinator, config_entry, name: str, unique_id_suffix: str):
        """
        初始化传感器基类
        
        Args:
            coordinator: IkuaiDataCoordinator 实例，负责数据更新
            config_entry: 配置入口对象，包含用户配置信息
            name: 传感器的显示名称（如 'CPU Usage'）
            unique_id_suffix: 唯一标识符后缀（用于生成全局唯一的 entity_id）
        
        Example:
            >>> sensor = IkuaiSensor(coordinator, config_entry, "CPU", "cpu")
            >>> print(sensor.name)  # 输出: "iKuai Router CPU"
        """
        self.coordinator = coordinator
        self.config_entry = config_entry
        self._name = name
        self._unique_id_suffix = unique_id_suffix

    @property
    def name(self) -> str:
        """
        返回传感器的显示名称
        
        Returns:
            str: 完整的传感器名称，格式为 "iKuai Router <名称>"
        
        Example:
            >>> sensor = IkuaiSensor(coordinator, config_entry, "CPU", "cpu")
            >>> print(sensor.name)  # 输出: "iKuai Router CPU"
        """
        return f"爱快路由器 {self._name}"  # 使用中文名称更友好

    @property
    def unique_id(self) -> str:
        """
        返回传感器的唯一标识符
        
        Returns:
            str: 全局唯一的传感器ID，格式为 "{entry_id}_{suffix}"
        
        This ID is used by Home Assistant to uniquely identify this entity.
        It ensures that sensors are not duplicated across different config entries.
        """
        return f"{self.config_entry.entry_id}_{self._unique_id_suffix}"

    @property
    def device_info(self):
        """
        返回设备信息，将传感器关联到爱快路由器这个物理设备
        
        Returns:
            DeviceInfo: 包含制造商、型号等元数据的对象
        
        This creates a logical device in Home Assistant that groups all sensors together.
        Users can see all sensor states under the 'iKuai Router' device page.
        """
        return DeviceInfo(
            identifiers={(DOMAIN, self.config_entry.entry_id)},  # 唯一标识符
            name="爱快路由器",                                   # 设备名称（中文）
            manufacturer="爱快",                                   # 制造商（中文）
            model="Router",                                        # 型号
        )

    @property
    def available(self) -> bool:
        """
        检查传感器是否可用
        
        Returns:
            bool: True 表示数据协调器已获取到有效的系统信息，否则为 False
        
        A sensor is considered unavailable if:
        - The coordinator has not fetched data yet (data is None)
        - The 'system' key is missing from the latest data update
        """
        return self.coordinator.data is not None and "system" in self.coordinator.data

    @property
    def should_poll(self) -> bool:
        """
        返回是否应该启用轮询
        
        Returns:
            bool: False，因为数据更新由协调器驱动，不需要额外轮询
        
        Home Assistant's DataUpdateCoordinator handles all data refreshes.
        Setting this to False prevents unnecessary polling overhead.
        """
        return False  # 不使用轮询，由协调器自动触发更新


class CpuSensor(IkuaiSensor):
    """
    CPU使用率传感器
    
    显示爱快路由器的当前CPU使用百分比。
    
    Attributes:
        unit_of_measurement: "%", 表示单位为百分比
    """

    def __init__(self, coordinator, config_entry):
        """
        初始化CPU传感器
        
        Args:
            coordinator: 数据协调器实例
            config_entry: 配置入口对象
        """
        # 调用父类构造函数，传递名称和唯一ID后缀
        super().__init__(coordinator, config_entry, "CPU使用率", "cpu")

    @property
    def state(self):
        """
        返回传感器的当前状态值（CPU使用率）
        
        Returns:
            float or None: CPU使用百分比，如果获取失败则返回None
        
        Example:
            >>> sensor = CpuSensor(coordinator, config_entry)
            >>> print(sensor.state)  # 输出: 25.0（表示25%）
        """
        try:
            # 从协调器数据中提取CPU使用率
            return self.coordinator.data["system"].get("cpu_usage")
        except (KeyError, TypeError):
            # 如果数据结构不符合预期，返回None表示不可用
            return None

    @property
    def unit_of_measurement(self) -> str:
        """
        返回传感器的单位
        
        Returns:
            str: "%", 表示百分比
        
        This unit is displayed in the Home Assistant frontend.
        """
        return "%"  # 使用百分号作为单位


class MemorySensor(IkuaiSensor):
    """
    内存使用率传感器
    
    显示爱快路由器的当前内存使用百分比。
    
    Attributes:
        unit_of_measurement: "%", 表示单位为百分比
    """

    def __init__(self, coordinator, config_entry):
        """
        初始化内存传感器
        
        Args:
            coordinator: 数据协调器实例
            config_entry: 配置入口对象
        """
        super().__init__(coordinator, config_entry, "内存使用率", "memory")

    @property
    def state(self):
        """
        返回传感器的当前状态值（内存使用率）
        
        Returns:
            float or None: 内存使用百分比，如果获取失败则返回None
        
        Example:
            >>> sensor = MemorySensor(coordinator, config_entry)
            >>> print(sensor.state)  # 输出: 50.0（表示50%）
        """
        try:
            return self.coordinator.data["system"].get("mem_usage")
        except (KeyError, TypeError):
            return None

    @property
    def unit_of_measurement(self) -> str:
        """
        返回传感器的单位（百分比）
        
        Returns:
            str: "%"
        """
        return "%"


class UptimeSensor(IkuaiSensor):
    """
    运行时间传感器
    
    显示爱快路由器自上次重启以来的运行时长。
    
    Note:
        This sensor returns a string representation of uptime (e.g., '1天2小时')
        instead of a numeric value, so it doesn't have a unit_of_measurement.
    """

    def __init__(self, coordinator, config_entry):
        """
        初始化运行时间传感器
        
        Args:
            coordinator: 数据协调器实例
            config_entry: 配置入口对象
        """
        super().__init__(coordinator, config_entry, "运行时间", "uptime")

    @property
    def state(self):
        """
        返回传感器的当前状态值（运行时间字符串）
        
        Returns:
            str or None: 格式化后的运行时间，如 '1天2小时3分钟'，如果获取失败则返回None
        
        Example:
            >>> sensor = UptimeSensor(coordinator, config_entry)
            >>> print(sensor.state)  # 输出: "2天5小时"
        """
        try:
            return self.coordinator.data["system"].get("uptime_str")
        except (KeyError, TypeError):
            return None


class WanIpSensor(IkuaiSensor):
    """
    WAN IP地址传感器
    
    显示爱快路由器当前WAN口的公网IP地址。
    
    Note:
        This is useful for monitoring if your router's public IP has changed.
    """

    def __init__(self, coordinator, config_entry):
        """
        初始化WAN IP传感器
        
        Args:
            coordinator: 数据协调器实例
            config_entry: 配置入口对象
        """
        super().__init__(coordinator, config_entry, "WAN IP地址", "wan_ip")

    @property
    def state(self):
        """
        返回传感器的当前状态值（IP地址）
        
        Returns:
            str or None: IPv4或IPv6地址字符串，如果获取失败则返回None
        
        Example:
            >>> sensor = WanIpSensor(coordinator, config_entry)
            >>> print(sensor.state)  # 输出: "203.0.113.1"
        """
        try:
            return self.coordinator.data["system"].get("wan_ip")
        except (KeyError, TypeError):
            return None


class OnlineUsersSensor(IkuaiSensor):
    """
    在线用户数量传感器
    
    显示当前连接到爱快路由器的设备总数。
    
    Attributes:
        unit_of_measurement: "个", 表示数量为设备个数
    """

    def __init__(self, coordinator, config_entry):
        """
        初始化在线用户数量传感器
        
        Args:
            coordinator: 数据协调器实例
            config_entry: 配置入口对象
        """
        super().__init__(coordinator, config_entry, "在线设备数", "online_users")

    @property
    def state(self):
        """
        返回传感器的当前状态值（在线用户数量）
        
        Returns:
            int or None: 在线用户总数，如果获取失败则返回None
        
        Example:
            >>> sensor = OnlineUsersSensor(coordinator, config_entry)
            >>> print(sensor.state)  # 输出: 5（表示有5个设备在线）
        """
        try:
            return self.coordinator.data.get("online_count")
        except KeyError:
            return None

    @property
    def unit_of_measurement(self) -> str:
        """
        返回传感器的单位（中文：个）
        
        Returns:
            str: "个"
        """
        return "个"  # 使用中文单位更友好


async def async_setup_entry(hass, config_entry, async_add_entities):
    """
    从配置入口设置传感器实体
    
    This function is called by Home Assistant when setting up the integration.
    It creates all sensor entities and adds them to Home Assistant's entity registry.
    
    Args:
        hass: Home Assistant 实例，用于管理实体注册
        config_entry: 配置入口对象，包含用户配置信息
        async_add_entities: 异步添加实体的回调函数
    
    This function creates the following sensors:
    - CpuSensor: CPU使用率
    - MemorySensor: 内存使用率
    - UptimeSensor: 运行时间
    - WanIpSensor: WAN IP地址
    - OnlineUsersSensor: 在线设备数量
    """
    # 从 hass.data 中获取已创建的协调器实例
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    
    # 定义所有要创建的传感器类型列表
    sensors = [
        CpuSensor(coordinator, config_entry),       # CPU使用率传感器
        MemorySensor(coordinator, config_entry),    # 内存使用率传感器
        UptimeSensor(coordinator, config_entry),    # 运行时间传感器
        WanIpSensor(coordinator, config_entry),     # WAN IP地址传感器
        OnlineUsersSensor(coordinator, config_entry),  # 在线用户数量传感器
    ]

    # 将所有传感器添加到 Home Assistant
    async_add_entities(sensors)