"""
Интерфейсы для слоя Domain.

Определяет контракты для различных компонентов системы.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from src.config import TargetServerConfig
    from src.domain.models import MeshtasticMessage


class IMessageParser(ABC):
    """Интерфейс для парсера сообщений."""

    @abstractmethod
    def parse(self, topic: str, payload: bytes) -> "MeshtasticMessage":
        """
        Парсит сообщение из MQTT.

        Args:
            topic: MQTT топик
            payload: Данные сообщения в байтах

        Returns:
            Распарсенное сообщение MeshtasticMessage
        """
        pass


class IMessageTransformer(ABC):
    """Интерфейс для трансформации сообщений."""

    @abstractmethod
    def transform(self, message: "MeshtasticMessage") -> Optional[Dict]:
        """
        Трансформирует сообщение в формат для отправки на целевой сервер.

        Args:
            message: Сообщение для трансформации

        Returns:
            Словарь с данными для отправки или None, если сообщение не должно быть отправлено
        """
        pass


class ITargetServerClient(ABC):
    """Интерфейс для клиента целевого сервера."""

    @abstractmethod
    async def send(self, data: Dict) -> bool:
        """
        Отправляет данные на целевой сервер.

        Args:
            data: Данные для отправки

        Returns:
            True, если отправка успешна, False в противном случае
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Закрывает соединение с сервером."""
        pass


class ITargetServerRepository(ABC):
    """Интерфейс для репозитория целевых серверов."""

    @abstractmethod
    def get_enabled_servers(self) -> List["TargetServerConfig"]:  # type: ignore
        """Возвращает список включенных целевых серверов."""
        pass

    @abstractmethod
    def get_servers_for_message_type(
        self, message_type: str
    ) -> List["TargetServerConfig"]:  # type: ignore
        """
        Возвращает список серверов, которые принимают указанный тип сообщений.

        Args:
            message_type: Тип сообщения

        Returns:
            Список конфигураций серверов
        """
        pass

