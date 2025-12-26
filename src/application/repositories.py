"""
Репозитории для работы с целевыми серверами.

Управляет конфигурацией и доступом к целевым серверам.
"""

from typing import List
from src.config import TargetServerConfig
from src.domain.interfaces import ITargetServerRepository


class TargetServerRepository(ITargetServerRepository):
    """Репозиторий целевых серверов."""

    def __init__(self, servers: List[TargetServerConfig]):
        """
        Создает репозиторий.

        Args:
            servers: Список конфигураций целевых серверов
        """
        self._servers = servers

    def get_enabled_servers(self) -> List[TargetServerConfig]:
        """Возвращает список включенных серверов."""
        return [s for s in self._servers if s.enable]

    def get_servers_for_message_type(
        self, message_type: str
    ) -> List[TargetServerConfig]:
        """
        Возвращает серверы, которые принимают указанный тип сообщений.

        Args:
            message_type: Тип сообщения

        Returns:
            Список конфигураций серверов
        """
        message_type_lower = message_type.lower()
        enabled_servers = self.get_enabled_servers()

        return [
            s
            for s in enabled_servers
            if message_type_lower in s.allowed_types
        ]

