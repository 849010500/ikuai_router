"""Device tracker platform for iKuai Router."""
import logging
from homeassistant.components.device_tracker.config_entry import ScannerEntity
from homeassistant.components.device_tracker.const import SourceType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    entities = []
    seen_ids = set()
    for user in coordinator.data.get("online_users", []):
        # 生成唯一ID并检查是否已存在
        ip = user.get('ip') or ''
        mac = user.get('mac') or ''
        identifier = ip or mac
        if not identifier or identifier in seen_ids:
            continue
        seen_ids.add(identifier)
        entities.append(IkuaiDeviceTracker(coordinator, config_entry, user))
    async_add_entities(entities, True)


class IkuaiDeviceTracker(CoordinatorEntity, ScannerEntity):

    def __init__(self, coordinator, config_entry, user_info):
        super().__init__(coordinator)
        self.config_entry = config_entry
        self._user = user_info

    @property
    def unique_id(self):
        ip = self._user.get('ip') or ''
        mac = self._user.get('mac') or ''
        identifier = ip or mac or 'unknown'
        return f"{self.config_entry.entry_id}_tracker_{identifier}"

    @property
    def name(self):
        return self._user.get("name", "Unknown Device")

    @property
    def ip_address(self):
        return self._user.get("ip")

    @property
    def mac_address(self):
        return self._user.get("mac")

    @property
    def source_type(self):
        return SourceType.ROUTER

    @property
    def is_connected(self):
        return True

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, self.config_entry.entry_id)},
            name="iKuai Router",
            manufacturer="iKuai",
            model="Router",
        )
