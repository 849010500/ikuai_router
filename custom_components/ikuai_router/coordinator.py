"""Data coordinator for iKuai Router."""

import asyncio
import json
import logging
import os
from datetime import timedelta
from pathlib import Path

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import ENV_IKUAI_CLI_BASE_URL, ENV_IKUAI_CLI_TOKEN, CMD_SYSTEM_MONITOR, CMD_ONLINE_USERS
from .downloader import IkuaiCliDownloader

_LOGGER = logging.getLogger(__name__)


class IkuaiDataCoordinator(DataUpdateCoordinator):

    def __init__(self, hass: HomeAssistant, config_entry):
        super().__init__(
            hass, _LOGGER, name="ikuai_router", update_interval=timedelta(seconds=30),
        )
        self.config_entry = config_entry
        self.config = config_entry.data

        # Set up binary path - either custom or auto-downloaded
        custom_binary_path = self.config.get("binary_path", "")
        if custom_binary_path:
            self._binary_path = custom_binary_path
            self._downloader = None
        else:
            # Use auto-download
            storage_dir = Path(hass.config.path("ikuai_router/bin"))
            self._downloader = IkuaiCliDownloader(hass, storage_dir)
            self._binary_path = str(self._downloader.binary_path)

    async def _ensure_binary(self):
        """Ensure ikuai-cli binary is available, downloading if needed."""
        if self._downloader and not self._downloader.is_installed:
            _LOGGER.info("ikuai-cli not found, downloading...")
            success = await self._downloader.ensure_installed()
            if not success:
                raise UpdateFailed("Failed to download ikuai-cli")
            _LOGGER.info("ikuai-cli downloaded successfully")

    async def _check_binary(self):
        """Check if the ikuai-cli binary exists and is executable."""
        # First ensure binary is downloaded if needed
        await self._ensure_binary()

        if not os.path.exists(self._binary_path):
            _LOGGER.error("ikuai-cli binary not found at: %s", self._binary_path)
            return False
        if not os.access(self._binary_path, os.X_OK):
            _LOGGER.error("ikuai-cli binary is not executable: %s", self._binary_path)
            return False
        return True

    async def _run_cli_command(self, command):
        """Run an ikuai-cli command."""
        if not await self._check_binary():
            raise UpdateFailed(f"ikuai-cli binary not found or not executable: {self._binary_path}")

        full_cmd = [self._binary_path] + command.split()
        env = os.environ.copy()
        env[ENV_IKUAI_CLI_BASE_URL] = self.config["base_url"]
        env[ENV_IKUAI_CLI_TOKEN] = self.config.get("token", "")

        _LOGGER.debug("Running command: %s", " ".join(full_cmd))

        try:
            process = await asyncio.create_subprocess_exec(
                *full_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, env=env,
            )
            stdout, stderr = await process.communicate()

            _LOGGER.debug("Command output: %s", stdout.decode())
            if stderr:
                _LOGGER.debug("Command stderr: %s", stderr.decode())

            if process.returncode != 0:
                error_msg = stderr.decode().strip()
                _LOGGER.error("Command failed with return code %d: %s", process.returncode, error_msg)
                raise UpdateFailed(f"CLI command failed: {error_msg}")

            output = stdout.decode().strip()
            if not output:
                _LOGGER.warning("Empty output from command: %s", command)
                return {}

            try:
                return json.loads(output)
            except json.JSONDecodeError as e:
                _LOGGER.error("Invalid JSON output: %s, error: %s, output: %s", command, e, output[:200])
                raise UpdateFailed(f"Invalid JSON from CLI: {e}")

        except FileNotFoundError:
            _LOGGER.error("ikuai-cli binary not found: %s", self._binary_path)
            raise UpdateFailed(f"ikuai-cli binary not found: {self._binary_path}")
        except PermissionError:
            _LOGGER.error("Permission denied for ikuai-cli: %s", self._binary_path)
            raise UpdateFailed(f"Permission denied for ikuai-cli: {self._binary_path}")

    async def _async_update_data(self):
        """Fetch data from ikuai router."""
        system = {}
        online_users = []

        # Try to get system info
        try:
            resp = await self._run_cli_command("monitor system --format json")
            _LOGGER.debug("System response: %s", resp)
            # Handle both data formats: {"sysinfo": {...}} or {"data": {...}}
            if "sysinfo" in resp:
                system = resp["sysinfo"]
            elif "data" in resp:
                system = resp["data"]
            else:
                # If neither key exists, use the whole response
                system = resp
            if not system:
                _LOGGER.warning("No system data in response: %s", resp)
        except Exception as e:
            _LOGGER.warning("Failed to fetch system info: %s", e)

        # Try to get online users
        try:
            resp = await self._run_cli_command(CMD_ONLINE_USERS)
            _LOGGER.debug("Users response: %s", resp)
            # Handle different data formats
            if isinstance(resp, list):
                users_data = resp
            elif isinstance(resp, dict):
                # Try different possible keys
                users_data = resp.get("data", resp.get("users", []))
            else:
                users_data = []

            if isinstance(users_data, list):
                for u in users_data:
                    if isinstance(u, dict):
                        # 确保每个用户都有唯一标识
                        user_id = u.get("id") or f"{u.get('ip_addr')}_{u.get('mac_addr')}"
                        if not user_id or user_id == "_":
                            # 如果没有唯一标识，使用索引或跳过
                            continue
                        online_users.append({
                            "id": user_id,
                            "ip": u.get("ip_addr"),
                            "mac": u.get("mac_addr"),
                            "name": u.get("username", "Unknown"),
                        })
            else:
                _LOGGER.warning("Unexpected users data format: %s", type(users_data))
        except Exception as e:
            _LOGGER.warning("Failed to fetch users: %s", e)

        _LOGGER.debug("Returning data: system=%s, online_users=%d", system, len(online_users))
        return {
            "system": system,
            "online_users": online_users,
            "online_count": len(online_users)
        }

    async def kick_device(self, ip_address):
        """Kick a device from the network."""
        try:
            resp = await self._run_cli_command(f"users kick --ip {ip_address} --format json")
            _LOGGER.info("Kick device response: %s", resp)
            return resp.get("Status") == "Success" or resp.get("Result") == "Success"
        except Exception as e:
            _LOGGER.error("Failed to kick device %s: %s", ip_address, e)
            return False

    async def async_close(self):
        """Close any open resources."""
        # We don't need to close the HA aiohttp session
        pass

