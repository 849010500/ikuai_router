"""Sensor platform for iKuai Router."""
import logging
from homeassistant.helpers.entity import Entity, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.sensor import SensorDeviceClass
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class IkuaiSensor(CoordinatorEntity, Entity):
    """基础传感器类"""

    def __init__(self, coordinator, config_entry, name, unique_id_suffix):
        super().__init__(coordinator)
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
        return DeviceInfo(
            identifiers={(DOMAIN, self.config_entry.entry_id)},
            name="iKuai Router",
            manufacturer="iKuai",
            model="Router"
        )

    @property
    def available(self):
        return self.coordinator.data is not None

    @property
    def should_poll(self):
        return False


# ============ 系统信息传感器 ============

class CpuSensor(IkuaiSensor):
    """CPU 使用率传感器"""
    def __init__(self, coordinator, config_entry):
        super().__init__(coordinator, config_entry, "CPU 使用率", "cpu")

    @property
    def icon(self):
        return "mdi:cpu-64-bit"

    @property
    def state(self):
        try:
            system = self.coordinator.data.get("system", {})
            if not system:
                return None
            if "cpu" in system:
                cpu_list = system["cpu"]
                if isinstance(cpu_list, list) and len(cpu_list) > 0:
                    total = 0.0
                    count = 0
                    for cpu_val in cpu_list:
                        if isinstance(cpu_val, str):
                            cpu_val = cpu_val.rstrip('%')
                        try:
                            total += float(cpu_val)
                            count += 1
                        except (ValueError, TypeError):
                            continue
                    if count > 0:
                        return round(total / count, 2)
            return system.get("cpu_usage")
        except (KeyError, TypeError, ZeroDivisionError):
            return None

    @property
    def unit_of_measurement(self):
        return "%"


class CpuTempSensor(IkuaiSensor):
    """CPU 温度传感器"""
    def __init__(self, coordinator, config_entry):
        super().__init__(coordinator, config_entry, "CPU 温度", "cpu_temp")

    @property
    def icon(self):
        return "mdi:thermometer"

    @property
    def state(self):
        try:
            system = self.coordinator.data.get("system", {})
            if not system:
                return None
            if "cputemp" in system:
                temp_list = system["cputemp"]
                if isinstance(temp_list, list) and len(temp_list) > 0:
                    total = 0.0
                    count = 0
                    for temp in temp_list:
                        try:
                            total += float(temp)
                            count += 1
                        except (ValueError, TypeError):
                            continue
                    if count > 0:
                        return round(total / count, 1)
            return system.get("cpu_temp")
        except (KeyError, TypeError, ZeroDivisionError):
            return None

    @property
    def unit_of_measurement(self):
        return "°C"

    @property
    def device_class(self):
        return SensorDeviceClass.TEMPERATURE


class MemoryUsageSensor(IkuaiSensor):
    """内存使用率传感器"""
    def __init__(self, coordinator, config_entry):
        super().__init__(coordinator, config_entry, "内存使用率", "memory_usage")

    @property
    def icon(self):
        return "mdi:memory"

    @property
    def state(self):
        try:
            system = self.coordinator.data.get("system", {})
            if not system:
                return None
            if "memory" in system:
                mem = system["memory"]
                if isinstance(mem, dict):
                    used = mem.get("used")
                    if isinstance(used, str) and "%" in used:
                        return used.rstrip('%')
                    total = mem.get("total", 0)
                    available = mem.get("available", 0)
                    if total > 0:
                        return round((total - available) / total * 100, 1)
            return system.get("mem_usage")
        except (KeyError, TypeError, ZeroDivisionError):
            return None

    @property
    def unit_of_measurement(self):
        return "%"

    @property
    def extra_state_attributes(self):
        """返回内存详细信息"""
        try:
            system = self.coordinator.data.get("system", {})
            if not system:
                return None
            if "memory" in system and isinstance(system["memory"], dict):
                mem = system["memory"]
                return {
                    "总内存": f"{round(mem.get('total', 0) / 1024 / 1024, 1)} GB",
                    "已用": f"{round((mem.get('total', 0) - mem.get('available', 0)) / 1024 / 1024, 1)} GB",
                    "可用": f"{round(mem.get('available', 0) / 1024 / 1024, 1)} GB",
                    "缓存": f"{round(mem.get('cached', 0) / 1024 / 1024, 1)} GB",
                    "缓冲": f"{round(mem.get('buffers', 0) / 1024 / 1024, 1)} GB",
                }
        except (KeyError, TypeError):
            pass
        return None


class UptimeSensor(IkuaiSensor):
    """运行时间传感器"""
    def __init__(self, coordinator, config_entry):
        super().__init__(coordinator, config_entry, "运行时间", "uptime")

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
                parts.append(f"{days}天")
            if hours > 0:
                parts.append(f"{hours}小时")
            if minutes > 0:
                parts.append(f"{minutes}分钟")
            if not parts:
                parts.append(f"{secs}秒")
            return " ".join(parts)
        except (ValueError, TypeError):
            return str(seconds)

    @property
    def state(self):
        try:
            system = self.coordinator.data.get("system", {})
            if not system:
                return None
            uptime = system.get("uptime")
            if uptime is not None:
                return self._format_uptime(uptime)
            return system.get("uptime_str")
        except (KeyError, TypeError):
            return None

    @property
    def extra_state_attributes(self):
        """返回原始秒数"""
        try:
            system = self.coordinator.data.get("system", {})
            if not system:
                return None
            uptime = system.get("uptime")
            if uptime is not None:
                return {"原始秒数": int(uptime)}
        except (KeyError, TypeError):
            pass
        return None


# ============ 网络状态传感器 ============

class UploadSpeedSensor(IkuaiSensor):
    """上传速度传感器"""
    def __init__(self, coordinator, config_entry):
        super().__init__(coordinator, config_entry, "上传速度", "upload_speed")

    @property
    def icon(self):
        return "mdi:upload-network"

    @property
    def state(self):
        try:
            system = self.coordinator.data.get("system", {})
            if not system:
                return None
            if "stream" in system:
                stream = system["stream"]
                upload = stream.get("upload", 0)
                return round(float(upload) / 1024, 2)  # 转换为 KB/s
            return None
        except (KeyError, TypeError, ValueError):
            return None

    @property
    def unit_of_measurement(self):
        return "KB/s"


class DownloadSpeedSensor(IkuaiSensor):
    """下载速度传感器"""
    def __init__(self, coordinator, config_entry):
        super().__init__(coordinator, config_entry, "下载速度", "download_speed")

    @property
    def icon(self):
        return "mdi:download-network"

    @property
    def state(self):
        try:
            system = self.coordinator.data.get("system", {})
            if not system:
                return None
            if "stream" in system:
                stream = system["stream"]
                download = stream.get("download", 0)
                return round(float(download) / 1024, 2)  # 转换为 KB/s
            return None
        except (KeyError, TypeError, ValueError):
            return None

    @property
    def unit_of_measurement(self):
        return "KB/s"


class TotalUploadSensor(IkuaiSensor):
    """总上传流量传感器"""
    def __init__(self, coordinator, config_entry):
        super().__init__(coordinator, config_entry, "总上传流量", "total_upload")

    @property
    def icon(self):
        return "mdi:upload-network"

    @property
    def state(self):
        try:
            system = self.coordinator.data.get("system", {})
            if not system:
                return None
            if "stream" in system:
                stream = system["stream"]
                total_up = stream.get("total_up", 0)
                return round(float(total_up) / 1024 / 1024 / 1024, 2)  # 转换为 GB
            return None
        except (KeyError, TypeError, ValueError):
            return None

    @property
    def unit_of_measurement(self):
        return "GB"


class TotalDownloadSensor(IkuaiSensor):
    """总下载流量传感器"""
    def __init__(self, coordinator, config_entry):
        super().__init__(coordinator, config_entry, "总下载流量", "total_download")

    @property
    def icon(self):
        return "mdi:download-network"

    @property
    def state(self):
        try:
            system = self.coordinator.data.get("system", {})
            if not system:
                return None
            if "stream" in system:
                stream = system["stream"]
                total_down = stream.get("total_down", 0)
                return round(float(total_down) / 1024 / 1024 / 1024, 2)  # 转换为 GB
            return None
        except (KeyError, TypeError, ValueError):
            return None

    @property
    def unit_of_measurement(self):
        return "GB"


class ConnectionCountSensor(IkuaiSensor):
    """连接数传感器"""
    def __init__(self, coordinator, config_entry):
        super().__init__(coordinator, config_entry, "连接数", "connection_count")

    @property
    def icon(self):
        return "mdi:connection"

    @property
    def state(self):
        try:
            system = self.coordinator.data.get("system", {})
            if not system:
                return None
            if "stream" in system:
                stream = system["stream"]
                return stream.get("connect_num", 0)
            return None
        except (KeyError, TypeError):
            return None

    @property
    def extra_state_attributes(self):
        """返回连接详情"""
        try:
            system = self.coordinator.data.get("system", {})
            if not system:
                return None
            if "stream" in system:
                stream = system["stream"]
                return {
                    "TCP连接数": stream.get("tcp_connect_num", 0),
                    "UDP连接数": stream.get("udp_connect_num", 0),
                    "ICMP连接数": stream.get("icmp_connect_num", 0),
                }
        except (KeyError, TypeError):
            pass
        return None


# ============ 接口信息传感器 ============

class WanIpSensor(IkuaiSensor):
    """WAN IP 传感器"""
    def __init__(self, coordinator, config_entry):
        super().__init__(coordinator, config_entry, "WAN IP", "wan_ip")

    @property
    def icon(self):
        return "mdi:ip-network"

    @property
    def state(self):
        try:
            system = self.coordinator.data.get("system", {})
            if not system:
                return None
            return system.get("wan_ip") or system.get("ip_addr")
        except (KeyError, TypeError):
            return None


class WanIpv6Sensor(IkuaiSensor):
    """WAN IPv6 传感器"""
    def __init__(self, coordinator, config_entry):
        super().__init__(coordinator, config_entry, "WAN IPv6", "wan_ipv6")

    @property
    def icon(self):
        return "mdi:ip-network"

    @property
    def state(self):
        try:
            system = self.coordinator.data.get("system", {})
            if not system:
                return None
            return system.get("wan_ipv6")
        except (KeyError, TypeError):
            return None


# ============ 终端统计传感器 ============

class OnlineUsersSensor(IkuaiSensor):
    """在线终端数传感器"""
    def __init__(self, coordinator, config_entry):
        super().__init__(coordinator, config_entry, "在线终端数", "online_users")

    @property
    def icon(self):
        return "mdi:account-group"

    @property
    def state(self):
        try:
            if "online_count" in self.coordinator.data:
                return self.coordinator.data["online_count"]
            system = self.coordinator.data.get("system", {})
            if not system:
                return None
            if "online_user" in system:
                online_user = system["online_user"]
                if isinstance(online_user, dict):
                    return online_user.get("count")
            return system.get("online_user_count")
        except (KeyError, TypeError):
            return None

    @property
    def unit_of_measurement(self):
        return "devices"

    @property
    def extra_state_attributes(self):
        """返回在线用户详情"""
        try:
            system = self.coordinator.data.get("system", {})
            if not system:
                return None
            if "online_user" in system and isinstance(system["online_user"], dict):
                online_user = system["online_user"]
                return {
                    "2.4G设备": online_user.get("count_2g", 0),
                    "5G设备": online_user.get("count_5g", 0),
                    "有线设备": online_user.get("count_wired", 0),
                    "无线设备": online_user.get("count_wireless", 0),
                }
        except (KeyError, TypeError):
            pass
        return None


class OnlineApSensor(IkuaiSensor):
    """AP 在线数传感器"""
    def __init__(self, coordinator, config_entry):
        super().__init__(coordinator, config_entry, "AP 在线数", "online_ap")

    @property
    def icon(self):
        return "mdi:router-wireless"

    @property
    def state(self):
        try:
            system = self.coordinator.data.get("system", {})
            if not system:
                return None
            if "online_ap" in system:
                return system["online_ap"]
            return None
        except (KeyError, TypeError):
            return None

    @property
    def unit_of_measurement(self):
        return "devices"


# ============ 设备信息传感器 ============

class HostnameSensor(IkuaiSensor):
    """主机名传感器"""
    def __init__(self, coordinator, config_entry):
        super().__init__(coordinator, config_entry, "主机名", "hostname")

    @property
    def icon(self):
        return "mdi:router"

    @property
    def state(self):
        try:
            system = self.coordinator.data.get("system", {})
            if not system:
                return None
            return system.get("hostname", "iKuai")
        except (KeyError, TypeError):
            return None


class VersionSensor(IkuaiSensor):
    """固件版本传感器"""
    def __init__(self, coordinator, config_entry):
        super().__init__(coordinator, config_entry, "固件版本", "version")

    @property
    def icon(self):
        return "mdi:information"

    @property
    def state(self):
        try:
            system = self.coordinator.data.get("system", {})
            if not system:
                return None
            if "verinfo" in system:
                verinfo = system["verinfo"]
                return verinfo.get("version")
            return None
        except (KeyError, TypeError):
            return None

    @property
    def extra_state_attributes(self):
        """返回版本详情"""
        try:
            system = self.coordinator.data.get("system", {})
            if not system:
                return None
            if "verinfo" in system and isinstance(system["verinfo"], dict):
                verinfo = system["verinfo"]
                return {
                    "架构": verinfo.get("arch"),
                    "系统位数": verinfo.get("sysbit"),
                    "构建日期": verinfo.get("build_date"),
                    "完整版本": verinfo.get("verstring"),
                }
        except (KeyError, TypeError):
            pass
        return None


async def async_setup_entry(hass, config_entry, async_add_entities):
    """设置传感器平台"""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    async_add_entities([
        # 系统信息
        CpuSensor(coordinator, config_entry),
        CpuTempSensor(coordinator, config_entry),
        MemoryUsageSensor(coordinator, config_entry),
        UptimeSensor(coordinator, config_entry),
        # 网络状态
        UploadSpeedSensor(coordinator, config_entry),
        DownloadSpeedSensor(coordinator, config_entry),
        TotalUploadSensor(coordinator, config_entry),
        TotalDownloadSensor(coordinator, config_entry),
        ConnectionCountSensor(coordinator, config_entry),
        # 接口信息
        WanIpSensor(coordinator, config_entry),
        WanIpv6Sensor(coordinator, config_entry),
        # 终端统计
        OnlineUsersSensor(coordinator, config_entry),
        OnlineApSensor(coordinator, config_entry),
        # 设备信息
        HostnameSensor(coordinator, config_entry),
        VersionSensor(coordinator, config_entry),
    ], True)