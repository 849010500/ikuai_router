"""Data coordinator for iKuai Router."""

import asyncio
import json
import logging
import os
import shutil
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import ENV_IKUAI_CLI_BASE_URL, ENV_IKUAI_CLI_TOKEN, CMD_SYSTEM_MONITOR, CMD_ONLINE_USERS

_LOGGER = logging.getLogger(__name__)


class IkuaiDataCoordinator(DataUpdateCoordinator):

    def __init__(self, hass, config_entry):
        super().__init__(
            hass, _LOGGER, name="ikuai_router", update_interval=timedelta(seconds=30),
        )
        self.config_entry = config_entry
        self.config = config_entry.data
        self._binary_path = self.config.get("binary_path", "/usr/local/bin/ikuai-cli")

    async def _check_binary(self):
        """Check if the ikuai-cli binary exists and is executable."""
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
            system = resp.get("data", {})
            if not system:
                _LOGGER.warning("No system data in response: %s", resp)
        except Exception as e:
            _LOGGER.warning("Failed to fetch system info: %s", e)

        # Try to get online users
        try:
            resp = await self._run_cli_command("users online --format json")
            _LOGGER.debug("Users response: %s", resp)
            users_data = resp.get("data", [])
            if isinstance(users_data, list):
                for u in users_data:
                    if isinstance(u, dict):
                        online_users.append({
                            "id": u.get("id"),
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
