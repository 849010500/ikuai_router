DOMAIN = "ikuai_router"
CONFIG_ENTRY_TITLE = "iKuai Router"
CONF_BASE_URL = "base_url"
CONF_TOKEN = "token"
CONF_BINARY_PATH = "binary_path"
ENV_IKUAI_CLI_BASE_URL = "IKUAI_CLI_BASE_URL"
ENV_IKUAI_CLI_TOKEN = "IKUAI_CLI_TOKEN"

# Default command templates
CMD_SYSTEM_MONITOR = "monitor system --format json"
CMD_CLIENTS_ONLINE = "monitor clients-online --format json --page 1 --page-size 200"
CMD_CLIENTS_IP6_ONLINE = "monitor clients-ip6-online --format json --page 1 --page-size 200"
CMD_WIRELESS_STATS = "monitor wireless-stats --format json"
CMD_INTERFACES = "monitor interfaces --format json"
CMD_INTERFACES_CONFIG = "monitor interfaces-config --format json"
CMD_INTERFACES_TRAFFIC_V6 = "monitor interfaces-traffic-v6 --format json"

