"""iKuai Router integration for Home Assistant."""
import asyncio
import logging
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "device_tracker", "switch", "binary_sensor"]


async def async_setup(hass: HomeAssistant, config):
    return True


async def async_setup_entry(hass: HomeAssistant, entry) -> bool:
    from .coordinator import IkuaiDataCoordinator

    try:
    coordinator = IkuaiDataCoordinator(hass, entry)
        # 首次数据获取，但允许失败
    await coordinator.async_refresh()
    except Exception as ex:
        _LOGGER.warning("首次数据获取失败，将在后台继续重试: %s", ex)
        # 即使首次失败，也继续设置，协调器会自动重试

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator}

    try:
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except Exception as ex:
        _LOGGER.error("平台设置失败: %s", ex)
        raise ConfigEntryNotReady(f"平台设置失败: {ex}") from ex

    return True


async def async_unload_entry(hass: HomeAssistant, entry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

