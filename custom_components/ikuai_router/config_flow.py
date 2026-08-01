"""Config flow for iKuai Router."""
from __future__ import annotations

import logging
import re
import ssl
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DOMAIN,
    CONFIG_ENTRY_TITLE,
    CONF_BASE_URL,
    CONF_TOKEN,
    CONF_BINARY_PATH,
)

_LOGGER = logging.getLogger(__name__)

# 爱快常见 API 端口（路由器 Web/API 管理端口，优先探测）
COMMON_PORTS = [8080, 443, 80, 8443, 9080, 9090, 88, 8081, 8000]

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_BASE_URL, default="http://192.168.1.1"): str,
        vol.Required(CONF_TOKEN): str,
        vol.Optional(CONF_BINARY_PATH, default=""): str,
    }
)


def _normalize_base_url(raw: str) -> str:
    """规范化 Base URL：自动补协议，去除尾部斜杠。"""
    url = raw.strip()
    if not url:
        return url
    if not re.match(r"^https?://", url, re.IGNORECASE):
        url = f"http://{url}"
    return url.rstrip("/")


def _extract_host(raw_url: str) -> str:
    """从 URL 中提取纯主机名（去掉协议、端口、路径）。"""
    url = _normalize_base_url(raw_url)
    host_part = re.sub(r"^https?://", "", url, flags=re.IGNORECASE).split("/")[0]
    # 去掉认证信息 user:pass@
    host_part = host_part.rsplit("@", 1)[-1]
    # 去掉端口
    host_part = re.sub(r":\d+$", "", host_part)
    return host_part


class IkuaiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for iKuai Router."""

    VERSION = 2

    def __init__(self) -> None:
        """Initialize flow."""
        self._temp_data: dict[str, Any] = {}
        self._reconfigure = False

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._temp_data = dict(user_input)
            base_url = user_input.get(CONF_BASE_URL, "")
            normalized = _normalize_base_url(base_url)
            self._temp_data[CONF_BASE_URL] = normalized

            # 如果没有显式指定端口 -> 自动探测
            if not re.search(r":\d+$", normalized):
                return await self.async_step_detect()

            return self._finish(self._temp_data)

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_detect(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """自动探测 iKuai API 端口。"""
        if user_input is not None:
            # 用户确认/修改了 URL
            self._temp_data.update(user_input)
            return self._finish(self._temp_data)

        host_only = _extract_host(self._temp_data.get(CONF_BASE_URL, ""))
        if not host_only:
            return self._finish(self._temp_data)

        detected_urls: list[str] = []
        session = async_get_clientsession(self.hass)
        ssl_ctx = None
        try:
            ssl_ctx = ssl.create_default_context()
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE
        except Exception:
            ssl_ctx = None

        tried: list[str] = []
        for port in COMMON_PORTS:
            scheme = "https" if port in (443, 8443) else "http"
            candidate = f"{scheme}://{host_only}:{port}"
            tried.append(candidate)
            try:
                timeout = aiohttp.ClientTimeout(total=3)
                async with session.get(
                    f"{candidate}/",
                    timeout=timeout,
                    ssl=ssl_ctx if ssl_ctx is not None else False,
                    allow_redirects=False,
                ) as resp:
                    _LOGGER.info("端口探测 %s 返回 HTTP %d", candidate, resp.status)
                    detected_urls.append(candidate)
                    if len(detected_urls) >= 3:
                        break
            except Exception as ex:
                _LOGGER.debug("端口探测 %s 失败: %s", candidate, ex)

        if not detected_urls:
            # 没有探测到 -> 让用户手动填写完整 URL（含端口）
            return self.async_show_form(
                step_id="detect",
                data_schema=vol.Schema(
                    {
                        vol.Required(
                            CONF_BASE_URL,
                            default=self._temp_data.get(CONF_BASE_URL, "http://192.168.1.1"),
                        ): str,
                        vol.Required(
                            CONF_TOKEN,
                            default=self._temp_data.get(CONF_TOKEN, ""),
                        ): str,
                        vol.Optional(
                            CONF_BINARY_PATH,
                            default=self._temp_data.get(CONF_BINARY_PATH, ""),
                        ): str,
                    }
                ),
                errors={"base_url": "cannot_connect"},
                description_placeholders={"tried": "\n".join(tried)},
            )

        # 展示检测到的端口，让用户选择
        options = "\n".join(f"✅ {u}" for u in detected_urls)
        return self.async_show_form(
            step_id="detect",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_BASE_URL, default=detected_urls[0]
                    ): str,
                    vol.Required(
                        CONF_TOKEN,
                        default=self._temp_data.get(CONF_TOKEN, ""),
                    ): str,
                    vol.Optional(
                        CONF_BINARY_PATH,
                        default=self._temp_data.get(CONF_BINARY_PATH, ""),
                    ): str,
                }
            ),
            description_placeholders={"tried": options},
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """支持重新配置已有集成。"""
        errors: dict[str, str] = {}

        entry = self._get_reconfigure_entry()
        existing: dict[str, Any] = dict(entry.data)
        self._reconfigure = True
        self._temp_data = dict(existing)

        if user_input is not None:
            self._temp_data.update(user_input)
            base_url = self._temp_data.get(CONF_BASE_URL, "")
            normalized = _normalize_base_url(base_url)
            self._temp_data[CONF_BASE_URL] = normalized

            if not re.search(r":\d+$", normalized):
                return await self.async_step_detect()

            return self._finish(self._temp_data)

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_BASE_URL,
                        default=existing.get(CONF_BASE_URL, "http://192.168.1.1"),
                    ): str,
                    vol.Required(
                        CONF_TOKEN, default=existing.get(CONF_TOKEN, "")
                    ): str,
                    vol.Optional(
                        CONF_BINARY_PATH,
                        default=existing.get(CONF_BINARY_PATH, ""),
                    ): str,
                }
            ),
            errors=errors,
        )

    def _finish(self, data: dict[str, Any]) -> FlowResult:
        """完成流程：创建或更新配置条目。"""
        data = dict(data)
        # Remove empty binary_path to use auto-download
        if not data.get(CONF_BINARY_PATH):
            data.pop(CONF_BINARY_PATH, None)

        if self._reconfigure:
            return self.async_update_reload_and_abort(
                self.hass, self.config_entry, data=data
            )

        return self.async_create_entry(title=CONFIG_ENTRY_TITLE, data=data)