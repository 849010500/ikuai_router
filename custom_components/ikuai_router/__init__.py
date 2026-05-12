"""iKuai Router integration for Home Assistant."""
import asyncio
import logging
from homeassistant.core import HomeAssistant
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config):
    return True


async def async_setup_entry(hass: HomeAssistant, entry) -> bool:
    from .coordinator import IkuaiDataCoordinator

    coordinator = IkuaiDataCoordinator(hass, entry)
    await coordinator.async_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator}

    for platform in ["sensor", "device_tracker", "switch", "binary_sensor"]:
        await hass.config_entries.async_forward_entry_setup(entry, platform)

    return True


async def async_unload_entry(hass: HomeAssistant, entry) -> bool:
    unload_ok = all(
        await asyncio.gather(
            hass.config_entries.async_forward_entry_unload(entry, "sensor"),
            hass.config_entries.async_forward_entry_unload(entry, "device_tracker"),
            hass.config_entries.async_forward_entry_unload(entry, "switch"),
            hass.config_entries.async_forward_entry_unload(entry, "binary_sensor"),
        )
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
