"""
配置流程模块

负责处理用户在 Home Assistant 界面上的爱快路由器配置输入。
包括：
- 首次添加集成时的配置表单（IP地址、Token、CLI路径）
- 后续修改配置时的选项表单（Token）
"""
import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, OptionsFlow
from homeassistant.core import callback
from .const import DOMAIN, CONFIG_ENTRY_TITLE, CONF_BASE_URL, CONF_TOKEN, CONF_BINARY_PATH, DEFAULT_BINARY_PATH

_LOGGER = logging.getLogger(__name__)


class IkuaiConfigFlow(ConfigFlow, domain=DOMAIN):
    """
    处理爱快路由器的配置流程
    """

    VERSION = 1
    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """
        处理用户步骤的配置表单
        """
        errors: dict[str, str] = {}
        if user_input is not None:
            return self.async_create_entry(title=CONFIG_ENTRY_TITLE, data=user_input)

        schema = vol.Schema({
            vol.Required(CONF_BASE_URL, default="http://192.168.1.1"): str,
            vol.Required(CONF_TOKEN): str,
            vol.Optional(CONF_BINARY_PATH, default=DEFAULT_BINARY_PATH): str,
        })

        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """
        返回选项流程处理器
        """
        return IkuaiOptionsFlowHandler(config_entry)


class IkuaiOptionsFlowHandler(OptionsFlow):
    """
    处理爱快路由器的选项配置流程
    """

    async def async_step_init(self, user_input=None):
        """
        处理选项步骤的表单
        """
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema({
            vol.Optional(CONF_TOKEN, default=self.config_entry.data.get(CONF_TOKEN, "")): str
        })
        
        return self.async_show_form(step_id="init", data_schema=schema)