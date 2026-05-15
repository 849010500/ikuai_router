"""Data coordinator for iKuai Router - Direct API Version."""

import asyncio
import hashlib
import json
import logging
import time
from datetime import timedelta
from urllib.parse import urljoin

import aiohttp
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import DOMAIN
_LOGGER = logging.getLogger(__name__)


class IkuaiDataCoordinator(DataUpdateCoordinator):

    def __init__(self, hass, config_entry):
        super().__init__(
            hass, _LOGGER, name="ikuai_router", update_interval=timedelta(seconds=30),
        )
        self.config_entry = config_entry
        self.config = config_entry.data
        self._base_url = self.config.get("base_url", "http://192.168.1.1").rstrip("/")
        self._username = self.config.get("username", "admin")
        self._password = self.config.get("password", "")
        self._token = self.config.get("token", "")
        self._session = None
        self._cookie = None

    async def _get_session(self):
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _login(self):
        """Login to iKuai router and get cookie."""
        session = await self._get_session()

        # Try to get salt first
        try:
            url = urljoin(self._base_url, "/Action/login")
            payload = {
                "username": self._username,
                "password": self._password,
            }

            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json()
                _LOGGER.debug("Login response: %s", data)

                if data.get("Result") == "Success" or data.get("Status") == "Success":
                    self._cookie = session.cookie_jar
                    _LOGGER.info("Login successful")
                    return True
                else:
                    _LOGGER.error("Login failed: %s", data)
                    return False
        except Exception as e:
            _LOGGER.error("Login error: %s", e)
            return False

    async def _api_call(self, method, action, param=None):
        """Make API call to iKuai router."""
        session = await self._get_session()

        url = urljoin(self._base_url, "/Action/call")

        payload = {
            "FuncName": method,
            "Action": action,
            "Param": param or {},
        }

        # Add token if available
        headers = {}
        if self._token:
            headers["Authorization"] = self._token
        try:
            async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json()
                _LOGGER.debug("API response for %s.%s: %s", method, action, data)
                return data
        except Exception as e:
            _LOGGER.error("API call error for %s.%s: %s", method, action, e)
            # Try to re-login
            await self._login()
            async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                return await resp.json()

    async def _fetch_system_info(self):
        """Fetch system information from router."""
        try:
            # Try direct API approach
            session = await self._get_session()

            # Method 1: Using /Action/call endpoint
            url = urljoin(self._base_url, "/Action/call")
            payload = {
                "FuncName": "SysInfo",
                "Action": "show",
                "Param": {}
            }

            headers = {}
            if self._token:
                headers["Authorization"] = self._token

            async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json()
                _LOGGER.debug("System info response: %s", data)

                if isinstance(data, dict):
                    if data.get("Result") == "Success":
                        return data.get("Data", {})
                    elif "data" in data:
                        return data["data"]
                    return data
        except Exception as e:
            _LOGGER.warning("Failed to fetch system info via API: %s", e)

        # Fallback: try alternative endpoint
        try:
            url = urljoin(self._base_url, "/SysInfo")
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                return await resp.json()
        except Exception as e:
            _LOGGER.error("All system info fetch attempts failed: %s", e)
            return {}

    async def _fetch_online_users(self):
        """Fetch online users from router."""
        try:
            session = await self._get_session()

            url = urljoin(self._base_url, "/Action/call")
            payload = {
                "FuncName": "MonitorLanIP",
                "Action": "show",
                "Param": {
                    "TYPE": "data,total",
                    "limit": "0,100",
                    "ORDER": "",
                    "ORDER_BY": "ip_addr_int",
                }
            }

            headers = {}
            if self._token:
                headers["Authorization"] = self._token

            async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json()
                _LOGGER.debug("Online users response: %s", data)

                users = []
                if isinstance(data, dict):
                    result = data.get("Data", data.get("data", []))
                    if isinstance(result, dict):
                        result = result.get("data", [])
                    if isinstance(result, list):
                        for u in result:
                            if isinstance(u, dict):
                                users.append({
                                    "id": u.get("id", ""),
                                    "ip": u.get("ip_addr", u.get("ip", "")),
                                    "mac": u.get("mac_addr", u.get("mac", "")),
                                    "name": u.get("hostname", u.get("username", "Unknown")),
                                })
                return users
        except Exception as e:
            _LOGGER.error("Failed to fetch online users: %s", e)
            return []

    async def _async_update_data(self):
        """Fetch data from ikuai router."""
        system = {}
        online_users = []

        # Get system info
        try:
            system = await self._fetch_system_info()
            _LOGGER.debug("System data: %s", system)
        except Exception as e:
            _LOGGER.warning("Failed to fetch system info: %s", e)

        # Get online users
        try:
            online_users = await self._fetch_online_users()
            _LOGGER.debug("Online users count: %d", len(online_users))
        except Exception as e:
            _LOGGER.warning("Failed to fetch online users: %s", e)

        return {
            "system": system,
            "online_users": online_users,
            "online_count": len(online_users)
        }

    async def kick_device(self, ip_address):
        """Kick a device from the network."""
        try:
            session = await self._get_session()

            url = urljoin(self._base_url, "/Action/call")
            payload = {
                "FuncName": "MonitorLanIP",
                "Action": "kick",
                "Param": {"ip_addr": ip_address}
            }

            headers = {}
            if self._token:
                headers["Authorization"] = self._token

            async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json()
                _LOGGER.info("Kick device response: %s", data)
                return data.get("Result") == "Success" or data.get("Status") == "Success"
        except Exception as e:
            _LOGGER.error("Failed to kick device %s: %s", ip_address, e)
            return False

    async def async_close(self):
        """Close the coordinator session."""
        if self._session and not self._session.closed:
            await self._session.close()

