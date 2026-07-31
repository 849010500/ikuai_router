"""Data coordinator for iKuai Router."""

import asyncio
import json
import logging
import os
import re
from datetime import timedelta
from pathlib import Path

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import ENV_IKUAI_CLI_BASE_URL, ENV_IKUAI_CLI_TOKEN, CMD_SYSTEM_MONITOR, CMD_CLIENTS_ONLINE, CMD_WIRELESS_STATS, CMD_INTERFACES, CMD_INTERFACES_CONFIG
from .downloader import IkuaiCliDownloader

_LOGGER = logging.getLogger(__name__)


class IkuaiDataCoordinator(DataUpdateCoordinator):

    def __init__(self, hass: HomeAssistant, config_entry):
        super().__init__(
            hass, _LOGGER, name="ikuai_router", update_interval=timedelta(seconds=5),
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

    def _extract_data(self, resp):
        """Extract data from response, handling different formats."""
        if isinstance(resp, dict):
            for key in ['data', 'sysinfo', 'result']:
                if key in resp:
                    return resp[key]
        return resp

    async def _async_update_data(self):
        """Fetch data from ikuai router."""
        system = {}
        online_users = []
        wireless_info = {}
        interfaces_info = {}

        # Try to get system info
        try:
            resp = await self._run_cli_command(CMD_SYSTEM_MONITOR)
            _LOGGER.debug("System response: %s", resp)
            system = self._extract_data(resp) or {}
            if not system:
                _LOGGER.warning("No system data in response: %s", resp)
        except Exception as e:
            _LOGGER.warning("Failed to fetch system info: %s", e)

        # Try to get interfaces info
        try:
            resp = await self._run_cli_command(CMD_INTERFACES)
            _LOGGER.debug("Interfaces response: %s", resp)
            interfaces_info = self._extract_data(resp) or {}
        except Exception as e:
            _LOGGER.warning("Failed to fetch interfaces info: %s", e)

        # Try to get interfaces config
        try:
            resp = await self._run_cli_command(CMD_INTERFACES_CONFIG)
            _LOGGER.debug("Interfaces config response: %s", resp)
            interfaces_config = self._extract_data(resp) or {}
            if isinstance(interfaces_config, dict):
                interfaces_info.update(interfaces_config)
            elif isinstance(interfaces_config, list):
                for iface in interfaces_config:
                    if isinstance(iface, dict):
                        name = iface.get('name', '')
                        if name:
                            interfaces_info[name] = iface
        except Exception as e:
            _LOGGER.warning("Failed to fetch interfaces config: %s", e)

        # Extract WAN IP and IPv6 from interfaces
        def _is_private_ip(ip_str: str) -> bool:
            """Check if an IP address is a private/internal address."""
            if not ip_str:
                return True
            parts = ip_str.split('.')
            if len(parts) != 4:
                return False
            try:
                first = int(parts[0])
                second = int(parts[1])
            except (ValueError, IndexError):
                return False
            if first == 10:
                return True
            if first == 172 and 16 <= second <= 31:
                return True
            if first == 192 and second == 168:
                return True
            if first == 127:
                return True
            return False

        def _find_wan_ip(interfaces_data):
            """Find the first non-private WAN IP from interfaces data."""
            if isinstance(interfaces_data, dict):
                items = interfaces_data.items()
            elif isinstance(interfaces_data, list):
                items = [(None, iface) for iface in interfaces_data]
            else:
                return None, None

            for key, value in items:
                if not isinstance(value, dict):
                    continue
                iface_name = (key or '').lower() if isinstance(key, str) else ''
                iface_name = iface_name or value.get('name', '').lower()
                if 'wan' not in iface_name and 'pppoe' not in iface_name:
                    continue
                # IPv4
                ip = value.get('ip') or value.get('ip_addr') or value.get('ipv4') or value.get('address')
                if ip and not _is_private_ip(ip):
                    return ip, None
                # IPv6
                ipv6 = value.get('ipv6') or value.get('ip6_addr') or value.get('ipv6_addr') or value.get('address6')
                if ipv6 and not _is_private_ip(ipv6):
                    return None, ipv6
            return None, None

        wan_ip, wan_ipv6 = _find_wan_ip(interfaces_info)
        if wan_ip and not system.get('wan_ip'):
            system['wan_ip'] = wan_ip
        if wan_ipv6 and not system.get('wan_ipv6'):
            system['wan_ipv6'] = wan_ipv6

        # Try to get wireless stats
        try:
            resp = await self._run_cli_command(CMD_WIRELESS_STATS)
            _LOGGER.debug("Wireless stats response: %s", resp)
            wireless_info = self._extract_data(resp) or {}
        except Exception as e:
            _LOGGER.warning("Failed to fetch wireless stats: %s", e)

        # Extract AP count from wireless info
        def _extract_ap_count(data):
            """Extract AP count from various possible response formats."""
            if isinstance(data, dict):
                # Try all possible field names for AP count
                for field in ['ap_count', 'ap_online', 'online_ap', 'total_ap', 'ap_total', 'ap_num', 'ap_count_total']:
                    val = data.get(field)
                    if val is not None:
                        try:
                            return int(val)
                        except (ValueError, TypeError):
                            continue
                # Check nested structures
                if 'ap_list' in data and isinstance(data['ap_list'], list):
                    return len(data['ap_list'])
                if 'ap_info' in data and isinstance(data['ap_info'], list):
                    return len(data['ap_info'])
                if 'wireless' in data and isinstance(data['wireless'], dict):
                    for field in ['ap_count', 'ap_online', 'online_ap', 'total_ap']:
                        val = data['wireless'].get(field)
                        if val is not None:
                            try:
                                return int(val)
                            except (ValueError, TypeError):
                                continue
            elif isinstance(data, list):
                return len(data)
            return None

        ap_count = _extract_ap_count(wireless_info)
        if ap_count is not None:
            system['online_ap'] = ap_count

        # Store interfaces and wireless info in system for extra attributes
        system['_interfaces'] = interfaces_info
        system['_wireless'] = wireless_info

        # Try to get online clients
        try:
            resp = await self._run_cli_command(CMD_CLIENTS_ONLINE)
            _LOGGER.debug("Clients response: %s", resp)
            clients_data = self._extract_data(resp) or []

            if isinstance(clients_data, list):
                seen_ids = set()
                for idx, u in enumerate(clients_data):
                    if isinstance(u, dict):
                        # 生成稳定的用户ID
                        mac = u.get('mac', '') or u.get('mac_addr', '') or ''
                        ip = u.get('ip', '') or u.get('ip_addr', '') or ''
                        hostname = u.get('hostname', '') or u.get('host', '') or u.get('name', '') or ''

                        # 优先使用MAC地址，其次IP，再次索引
                        if mac:
                            user_id = f"mac_{mac}"
                        elif ip:
                            user_id = f"ip_{ip}"
                        else:
                            user_id = f"idx_{idx}"

                        # 跳过重复的用户
                        if user_id in seen_ids:
                            continue
                        seen_ids.add(user_id)
                        online_users.append({
                            "id": user_id,
                            "ip": ip,
                            "mac": mac,
                            "name": hostname or ip or "Unknown",
                        })
            else:
                _LOGGER.warning("Unexpected clients data format: %s", type(clients_data))
        except Exception as e:
            _LOGGER.warning("Failed to fetch clients: %s", e)

        _LOGGER.debug("Returning data: system=%s, online_users=%d", system, len(online_users))
        return {
            "system": system,
            "online_users": online_users,
            "online_count": len(online_users)
        }

    async def kick_device(self, ip_address):
        """Kick a device from the network."""
        # Validate IP address format to prevent command injection
        if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip_address):
            _LOGGER.error("Invalid IP address format: %s", ip_address)
            return False
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

