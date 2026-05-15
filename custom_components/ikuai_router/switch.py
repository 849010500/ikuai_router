"""Switch platform for iKuai Router."""
import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    entities = []
    for user in coordinator.data.get("online_users", []):
        entities.append(IkuaiKickSwitch(coordinator, config_entry, user))
    async_add_entities(entities)


class IkuaiKickSwitch(SwitchEntity):

    def __init__(self, coordinator, config_entry, user_info):
        self.coordinator = coordinator
        self.config_entry = config_entry
        self._user = user_info
        self._is_on = True

    @property
    def unique_id(self):
        return f"{self.config_entry.entry_id}_kick_{self._user.get('ip', 'unknown')}"

    @property
    def name(self):
        return f"Kick {self._user.get('name', 'Unknown')}"

    @property
    def is_on(self):
        return self._is_on

    async def async_turn_on(self, **kwargs):
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        _LOGGER.info("Kicking device: %s", self._user.get("ip"))
        try:
            success = await self.coordinator.kick_device(self._user.get("ip"))
            if success:
            self._is_on = False
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error("Failed to kick device: %s", self._user.get("ip"))
        except Exception as e:
            _LOGGER.error("Failed to kick device: %s", e)

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, self.config_entry.entry_id)},
            name="iKuai Router",
            manufacturer="iKuai",
            model="Router",
        )

