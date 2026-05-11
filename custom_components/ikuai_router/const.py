"""
Constants for the iKuai Router integration.

This module defines configuration keys, default values, and environment variable names 
used across the integration to communicate with the external 'ikuai-cli' tool.
"""

DOMAIN = "ikuai_router"  # Unique identifier for this integration in Home Assistant
CONFIG_ENTRY_TITLE = "iKuai Router"  # Display name in HA UI

# Configuration keys defined by the user during setup
CONF_BASE_URL = "base_url"       # The IP/URL of the iKuai router (e.g., http://192.168.1.1)
CONF_TOKEN = "token"             # API Token obtained from the router's web interface
CONF_BINARY_PATH = "binary_path" # Path to the executable 'ikuai-cli' binary

DEFAULT_BINARY_PATH = "/usr/local/bin/ikuai-cli"  # Fallback path if user doesn't specify one

# Environment variables used internally by subprocess calls to ikuai-cli.
# These allow us to pass credentials securely without modifying global shell env vars permanently.
ENV_IKUAI_CLI_BASE_URL = "IKUAI_CLI_BASE_URL"
ENV_IKUAI_CLI_TOKEN = "IKUAI_CLI_TOKEN"