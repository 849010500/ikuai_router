"""Data coordinator for iKuai Router."""
import asyncio
import json
import logging
import os
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import ENV_IKUAI_CLI_BASE_URL, ENV_IKUAI_CLI_TOKEN

_LOGGER = logging.getLogger(__name__)


class IkuaiDataCoordinator(DataUpdateCoordinator):

    def __init__(self, hass, config_entry):
        super().__init__(
            hass, _LOGGER, name="ikuai_router", update_interval=timedelta(seconds=30),
        )
        self.config_entry = config_entry
        self.config = config_entry.data

    async def _run_cli_command(self, command):
        full_cmd = [self.config.get("binary_path", "/usr/local/bin/ikuai-cli")] + command.split()
        env = os.environ.copy()
        env[ENV_IKUAI_CLI_BASE_URL] = self.config["base_url"]
        env[ENV_IKUAI_CLI_TOKEN] = self.config.get("token", "")
        process = await asyncio.create_subprocess_exec(
            *full_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, env=env,
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            raise UpdateFailed(stderr.decode())
        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            raise UpdateFailed("Invalid JSON from CLI")

    async def _async_update_data(self):
        system = {}
        online_users = []
        try:
            resp = await self._run_cli_command("monitor system --format json")
            system = resp.get("data", {})
        except Exception as e:
            _LOGGER.warning("Failed to fetch system info: %s", e)
        try:
            resp = await self._run_cli_command("users online --format json")
            for u in resp.get("data", []):
                if isinstance(u, dict):
                    online_users.append({
                        "id": u.get("id"), "ip": u.get("ip_addr"),
                        "mac": u.get("mac_addr"), "name": u.get("username", "Unknown"),
                    })
        except Exception as e:
            _LOGGER.warning("Failed to fetch users: %s", e)
        return {"system": system, "online_users": online_users, "online_count": len(online_users)}

