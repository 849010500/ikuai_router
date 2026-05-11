"""
开关实体模块

提供对爱快路由器的控制功能，目前实现了：
- 踢除在线用户（通过调用 ikuai-cli users online kick <id>）
每个在线用户都会生成一个对应的开关实体，点击后执行踢人操作。
"""
import logging
from homeassistant.components.switch import SwitchEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class IkuaiSwitch(SwitchEntity):
    """
    爱快路由器控制开关实体

    每个在线用户对应一个此类的实例，点击后会执行踢除该用户的操作。
    虽然名为 Switch（开关），但实际上是一个一次性触发的按钮式开关。
    """

    def __init__(self, coordinator, user_id: str, username: str, config_entry):
        """
        初始化控制开关

        Args:
            coordinator: 数据协调器实例，用于执行 CLI 命令和获取最新数据
            user_id: 要踢除的用户的唯一 ID（来自 ikuai-cli 返回的数据）
            username: 用户名或设备名称，用于显示在 HA UI 中
            config_entry: 配置条目对象
        """
        super().__init__()          # 调用父类初始化
        self.coordinator = coordinator  # 存储协调器引用以执行命令
        self.user_id = user_id      # 保存用户 ID（用于踢人操作）
        self._username = username   # 保存用户名（用于显示名称）
        self.config_entry = config_entry  # 保存配置条目引用

    @property
    def name(self) -> str:
        """
        返回开关的完整显示名称

        Returns:
            str: 格式为 "Kick {用户名}" 的显示名称
        """
        return f"踢出 {self._username}"  # 改为中文更友好

    @property
    def unique_id(self) -> str:
        """
        返回此开关的唯一标识符

        Returns:
            str: 格式化为 "{entry_id}_kick_{user_id}" 的唯一 ID
        """
        return f"{self.config_entry.entry_id}_kick_{self.user_id}"

    async def async_turn_on(self, **kwargs):
        """
        执行踢除用户操作

        当用户在 HA UI 中点击此开关时调用。会：
        1. 构建并执行 CLI 命令：users online kick {user_id}
        2. 记录日志信息
        3. 强制刷新协调器数据以更新状态（踢人后用户应立即从在线列表中消失）
        
        Args:
            **kwargs: 额外的关键字参数（通常为空）
        """
        try:
            # 通过协调器执行 CLI 命令：users online kick {user_id}
            await self.coordinator._run_cli_command(f"users online kick {self.user_id}")
            _LOGGER.info(f"已踢除用户 ID {self.user_id} ({self._username})")
            # 强制刷新数据以立即更新状态
            await self.coordinator.async_request_refresh()
        except Exception as e:
            # 如果执行失败，记录错误日志
            _LOGGER.error(f"踢除用户失败: {e}")

    @property
    def is_on(self) -> bool:
        """
        返回此开关的当前状态

        Returns:
            bool: True 表示用户在在线列表中，False 表示用户已离线
        """
        users = self.coordinator.data.get("online_users", [])
        # 检查是否有匹配该 user_id 的在线用户
        return any(u.get("id") == str(self.user_id) for u in users)

    @property
    def available(self) -> bool:
        """
        返回此开关是否可用

        Returns:
            bool: True（始终返回 True，让 HA 根据协调器状态自动判断可用性）
        """
        return True


async def async_setup_entry(hass, config_entry, async_add_entities):
    """
    从配置条目设置爱快控制开关

    Args:
        hass: Home Assistant 实例
        config_entry: 当前配置条目对象
        async_add_entities: 添加实体的回调函数
    """
    # 从 hass.data 获取协调器
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    
    entities = []
    if coordinator.data and "online_users" in coordinator.data:
        for user_data in coordinator.data["online_users"]:
            uid = user_data.get("id")              # 获取用户 ID
            uname = user_data.get("name", f"User_{uid}")  # 获取用户名，如果没有则使用默认名称
            # 只有当用户有有效 ID 时才创建开关（确保能正确执行踢人命令）
            if uid is not None:
                entities.append(IkuaiSwitch(coordinator, uid, uname, config_entry))

    # 将所有创建的开关实体添加到 Home Assistant
    async_add_entities(entities)