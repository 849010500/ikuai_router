"""Device tracker platform for iKuai Router."""
import logging
from homeassistant.components.device_tracker import DeviceScanner
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    entities = []
    for user in coordinator.data.get("online_users", []):
        entities.append(IkuaiDeviceTracker(coordinator, config_entry, user))
    async_add_entities(entities)


class IkuaiDeviceTracker(DeviceScanner):

    def __init__(self, coordinator, config_entry, user_info):
        self.coordinator = coordinator
        self.config_entry = config_entry
        self._user = user_info

    @property
    def unique_id(self):
        return f"{self.config_entry.entry_id}_tracker_{self._user.get('ip', 'unknown')}"

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
        return "router"

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
