"""Config flow for iKuai Router."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONFIG_ENTRY_TITLE,
    CONF_BASE_URL,
    CONF_TOKEN,
    CONF_BINARY_PATH,
)

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_BASE_URL, default="http://192.168.1.1"): str,
        vol.Required(CONF_TOKEN): str,
        vol.Optional(CONF_BINARY_PATH, default=""): str,
    }
)


class IkuaiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for iKuai Router."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Remove empty binary_path to use auto-download
            if not user_input.get(CONF_BINARY_PATH):
                user_input.pop(CONF_BINARY_PATH, None)
            return self.async_create_entry(title=CONFIG_ENTRY_TITLE, data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )