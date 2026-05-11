"""Config flow for iKuai Router."""
import logging

import voluptuous as vol

from homeassistant import config_entries

from .const import (
    DOMAIN,
    CONFIG_ENTRY_TITLE,
    CONF_BASE_URL,
    CONF_TOKEN,
    CONF_BINARY_PATH,
    DEFAULT_BINARY_PATH,
)

_LOGGER = logging.getLogger(__name__)


DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_BASE_URL, default="http://192.168.1.1"): str,
        vol.Required(CONF_TOKEN): str,
        vol.Optional(CONF_BINARY_PATH, default=DEFAULT_BINARY_PATH): str,
    }
)


class IkuaiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title=CONFIG_ENTRY_TITLE,
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
        )
