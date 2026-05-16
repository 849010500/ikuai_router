"""Sensor platform for iKuai Router."""
import logging
from homeassistant.helpers.entity import Entity, DeviceInfo
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class IkuaiSensor(Entity):

    def __init__(self, coordinator, config_entry, name, unique_id_suffix):
        self.coordinator = coordinator
        self.config_entry = config_entry
        self._name = name
        self._unique_id_suffix = unique_id_suffix

    @property
    def name(self):
        return f"iKuai {self._name}"

    @property
    def unique_id(self):
        return f"{self.config_entry.entry_id}_{self._unique_id_suffix}"

    @property
    def device_info(self):
        return DeviceInfo(identifiers={(DOMAIN, self.config_entry.entry_id)}, name="iKuai Router", manufacturer="iKuai", model="Router")

    @property
    def available(self):
        return self.coordinator.data is not None and "system" in self.coordinator.data

    @property
    def should_poll(self):
        return False


class CpuSensor(IkuaiSensor):
    def __init__(self, coordinator, config_entry):
        super().__init__(coordinator, config_entry, "CPU Usage", "cpu")

    @property
    def icon(self):
        return "mdi:cpu-64-bit"
    @property
    def state(self):
        try:
            system = self.coordinator.data["system"]
            # 处理新的 sysinfo 格式
            if "cpu" in system:
                cpu_list = system["cpu"]
                if isinstance(cpu_list, list) and len(cpu_list) > 0:
                    # 计算平均值
                    total = 0.0
                    for cpu_val in cpu_list:
                        if isinstance(cpu_val, str):
                            cpu_val = cpu_val.rstrip('%')
                        try:
                            total += float(cpu_val)
                        except (ValueError, TypeError):
                            continue
                    return round(total / len(cpu_list), 2)
            # 旧格式
            return system.get("cpu_usage")
        except (KeyError, TypeError, ZeroDivisionError):
            return None

    @property
    def unit_of_measurement(self):
        return "%"


class MemorySensor(IkuaiSensor):
    def __init__(self, coordinator, config_entry):
        super().__init__(coordinator, config_entry, "Memory Usage", "memory")

    @property
    def icon(self):
        return "mdi:memory"

    @property
    def state(self):
        try:
            system = self.coordinator.data["system"]
            # 处理新的 sysinfo 格式
            if "memory" in system:
                mem = system["memory"]
                if isinstance(mem, dict):
                    # 检查是否有 used 百分比
                    used = mem.get("used")
                    if isinstance(used, str) and "%" in used:
                        return used.rstrip('%')
                    # 计算百分比
                    total = mem.get("total", 0)
                    available = mem.get("available", 0)
                    if total > 0:
                        return round((total - available) / total * 100, 2)
            # 旧格式
            return system.get("mem_usage")
        except (KeyError, TypeError, ZeroDivisionError):
            return None

    @property
    def unit_of_measurement(self):
        return "%"


class UptimeSensor(IkuaiSensor):
    def __init__(self, coordinator, config_entry):
        super().__init__(coordinator, config_entry, "Uptime", "uptime")

    @property
    def icon(self):
        return "mdi:clock-outline"

    def _format_uptime(self, seconds):
        """将秒数转换为可读的运行时间格式"""
        try:
            seconds = int(seconds)
            days = seconds // 86400
            hours = (seconds % 86400) // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60

            parts = []
            if days > 0:
                parts.append(f"{days}d")
            if hours > 0:
                parts.append(f"{hours}h")
            if minutes > 0:
                parts.append(f"{minutes}m")
            if not parts:
                parts.append(f"{secs}s")
            return " ".join(parts)
        except (ValueError, TypeError):
            return str(seconds)

    @property
    def state(self):
        try:
            system = self.coordinator.data["system"]
            # 处理新的 sysinfo 格式 - uptime 是秒数
            uptime = system.get("uptime")
            if uptime is not None:
                return self._format_uptime(uptime)
            # 旧格式
            return system.get("uptime_str")
        except (KeyError, TypeError):
            return None


class WanIpSensor(IkuaiSensor):
    def __init__(self, coordinator, config_entry):
        super().__init__(coordinator, config_entry, "WAN IP", "wan_ip")

    @property
    def icon(self):
        return "mdi:ip-network"

    @property
    def state(self):
        try:
            system = self.coordinator.data["system"]
            # 处理新的 sysinfo 格式 - ip_addr 是路由器 IP
            return system.get("wan_ip") or system.get("ip_addr")
        except (KeyError, TypeError):
            return None


class OnlineUsersSensor(IkuaiSensor):
    def __init__(self, coordinator, config_entry):
        super().__init__(coordinator, config_entry, "Online Users", "online_users")

    @property
    def icon(self):
        return "mdi:account-group"

    @property
    def state(self):
        try:
            # 首先检查 coordinator.data["online_count"]（由 coordinator 计算）
            if "online_count" in self.coordinator.data:
                return self.coordinator.data["online_count"]
            # 然后检查系统数据中的在线用户数
            system = self.coordinator.data["system"]
            if "online_user" in system:
                online_user = system["online_user"]
                if isinstance(online_user, dict):
                    return online_user.get("count")
            # 旧格式
            return system.get("online_user_count")
        except (KeyError, TypeError):
            return None

    @property
    def unit_of_measurement(self):
        return "devices"


async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    async_add_entities([
        CpuSensor(coordinator, config_entry),
        MemorySensor(coordinator, config_entry),
        UptimeSensor(coordinator, config_entry),
        WanIpSensor(coordinator, config_entry),
        OnlineUsersSensor(coordinator, config_entry),
    ])

