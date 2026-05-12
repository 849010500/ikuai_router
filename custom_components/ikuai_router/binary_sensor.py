"""Binary sensor platform for iKuai Router."""
import logging
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    async_add_entities([IkuaiStatusSensor(coordinator, config_entry)])


class IkuaiStatusSensor(BinarySensorEntity):

    def __init__(self, coordinator, config_entry):
        self.coordinator = coordinator
        self.config_entry = config_entry

    @property
    def unique_id(self):
        return f"{self.config_entry.entry_id}_status"

    @property
    def name(self):
        return "iKuai Router Status"

    @property
    def is_on(self):
        return self.coordinator.data is not None and "system" in self.coordinator.data

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, self.config_entry.entry_id)},
            name="iKuai Router",
            manufacturer="iKuai",
            model="Router",
        )
