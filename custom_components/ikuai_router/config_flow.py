"""
配置流程模块

负责处理用户在 Home Assistant 界面上的爱快路由器配置输入。
包括：
- 首次添加集成时的配置表单（IP地址、CLI路径）
- 后续修改配置时的选项表单（Token）
"""
import logging
from typing import Any

import voluptuous as vol  # Home Assistant 使用的数据验证库
from homeassistant.config_entries import ConfigFlow, OptionsFlow
from homeassistant.core import callback
from .const import DOMAIN, CONFIG_ENTRY_TITLE, CONF_BASE_URL, CONF_TOKEN, CONF_BINARY_PATH, DEFAULT_BINARY_PATH

_LOGGER = logging.getLogger(__name__)


class IkuaiConfigFlow(ConfigFlow, domain=DOMAIN):
    """
    处理爱快路由器的配置流程
    
    ConfigFlow 负责引导用户完成首次配置，包括输入路由器IP、CLI工具路径等信息。
    """

    VERSION = 1  # 配置入口的版本号，用于后续升级

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """
        处理用户步骤的配置表单
        
        Args:
            user_input: 用户提交的表单数据。第一次访问时为None，提交后为包含表单数据的字典
        
        Returns:
            ConfigFlowHandlerResponse: 返回下一步的响应（显示表单或创建配置入口）
        
        This is the main entry point for configuration.
        Users will input their router IP and optionally override the CLI binary path.
        """
        errors: dict[str, str] = {}  # 用于存储错误信息

        if user_input is not None:
            # 用户提交了表单，创建配置入口
            return self.async_create_entry(title=CONFIG_ENTRY_TITLE, data=user_input)

        # 定义表单模式（Schema）
        schema = vol.Schema({
            # 必填字段：路由器IP地址，默认值为192.168.1.1
            vol.Required(CONF_BASE_URL, default="http://192.168.1.1"): str,
            # 可选字段：CLI工具路径，默认使用标准路径
            vol.Optional(CONF_BINARY_PATH, default=DEFAULT_BINARY_PATH): str,
        })

        # 显示配置表单供用户填写
        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """
        返回选项流程处理器
        
        Args:
            config_entry: 当前的配置入口对象
        
        Returns:
            ConfigFlowHandler: 处理后续配置修改的类实例
        
        This method is called when the user wants to modify the configuration.
        It returns an OptionsFlowHandler instance for handling option changes.
        """
        return IkuaiOptionsFlowHandler(config_entry)


class IkuaiOptionsFlowHandler(OptionsFlow):
    """
    处理爱快路由器的选项配置流程
    
    OptionsFlow 负责处理用户修改配置（如更新Token）的操作。
    """

    def __init__(self, config_entry):
        """
        初始化选项流程处理器
        
        Args:
            config_entry: 当前的配置入口对象，包含已保存的配置数据
        """
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """
        处理选项步骤的表单
        
        Args:
            user_input: 用户提交的表单数据。第一次访问时为None，提交后为包含表单数据的字典
        
        Returns:
            ConfigFlowHandlerResponse: 返回下一步的响应（显示表单或保存配置）
        
        This is called when the user clicks 'Configure Entry' in HA UI.
        Users can update their API token here.
        """
        if user_input is not None:
            # 用户提交了表单，保存新的Token
            return self.async_create_entry(title="", data=user_input)

        # 定义选项表单模式：只允许修改Token（因为IP和CLI路径通常不需要频繁更改）
        schema = vol.Schema({
            # Token字段，从已保存的配置中获取默认值
            vol.Optional(CONF_TOKEN, default=self.config_entry.data.get(CONF_TOKEN)): str
        })
        
        # 显示选项表单供用户填写
        return self.async_show_form(step_id="init", data_schema=schema)