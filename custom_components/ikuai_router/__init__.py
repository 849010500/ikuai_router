"""iKuai Router integration for Home Assistant."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import entity_registry as er
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "binary_sensor"]

# 已移除的平台（v0.1.46 起）
_REMOVED_PLATFORMS = {"switch", "device_tracker"}


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    return True


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """迁移配置条目：清理已移除平台的实体。"""
    old_version = config_entry.version
    _LOGGER.info("迁移配置条目 v%d -> v%d", old_version, 2)

    if old_version < 2:
        # 移除已删除平台的实体
        entity_registry = er.async_get(hass)
        registry_entries = er.async_entries_for_config_entry(
            entity_registry, config_entry.entry_id
        )
        removed_count = 0
        for entry in registry_entries:
            if entry.platform in _REMOVED_PLATFORMS:
                entity_registry.async_remove(entry.entity_id)
                _LOGGER.info("移除已废弃的实体: %s (platform=%s)", entry.entity_id, entry.platform)
                removed_count += 1
        if removed_count:
            _LOGGER.info("已从 registry 中移除 %d 个已废弃实体", removed_count)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
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

