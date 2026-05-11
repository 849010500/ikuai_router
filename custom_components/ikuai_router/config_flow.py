"""
配置流程模块
"""
import logging
from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN, CONFIG_ENTRY_TITLE, CONF_BASE_URL, CONF_TOKEN, CONF_BINARY_PATH, DEFAULT_BINARY_PATH

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema({
            vol.Required(CONF_BASE_URL, default="http://192.168.1.1"): str,
            vol.Required(CONF_TOKEN): str,
            vol.Optional(CONF_BINARY_PATH, default=DEFAULT_BINARY_PATH): str,
        })


class IkuaiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title=CONFIG_ENTRY_TITLE, data=user_input)

        return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return IkuaiOptionsFlowHandler(config_entry)


class IkuaiOptionsFlowHandler(config_entries.OptionsFlow):

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema({
            vol.Optional(CONF_TOKEN, default=self.config_entry.data.get(CONF_TOKEN, "")): str
        })
        
        return self.async_show_form(step_id="init", data_schema=schema)
