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
            return self.coordinator.data["system"].get("cpu_usage")
        except (KeyError, TypeError):
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
            return self.coordinator.data["system"].get("mem_usage")
        except (KeyError, TypeError):
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

    @property
    def state(self):
        try:
            return self.coordinator.data["system"].get("uptime_str")
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
            return self.coordinator.data["system"].get("wan_ip")
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
            return self.coordinator.data.get("online_count")
        except KeyError:
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

