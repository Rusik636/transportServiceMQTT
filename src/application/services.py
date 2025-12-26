"""
Сервисы приложения.

Оркестрирует обработку сообщений и отправку на целевые серверы.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional

from src.domain.models import MeshtasticMessage
from src.domain.interfaces import IMessageParser, IMessageTransformer
from src.config import TargetServerConfig
from src.infrastructure.http_client import TargetServerHTTPClient
from src.application.repositories import TargetServerRepository
from src.application.transformers import MessageTransformer

logger = logging.getLogger(__name__)


class MessageProcessingService:
    """Сервис обработки сообщений."""

    def __init__(
        self,
        parser: IMessageParser,
        transformer: IMessageTransformer,
        repository: TargetServerRepository,
        default_impedance_key: str = "default",
    ):
        """
        Создает сервис обработки сообщений.

        Args:
            parser: Парсер сообщений
            transformer: Трансформатор сообщений
            repository: Репозиторий целевых серверов
            default_impedance_key: Ключ импедантности по умолчанию
        """
        self.parser = parser
        self.transformer = transformer
        self.repository = repository
        self.default_impedance_key = default_impedance_key
        self._clients: Dict[str, TargetServerHTTPClient] = {}

    def _get_or_create_client(
        self, config: TargetServerConfig
    ) -> TargetServerHTTPClient:
        """
        Получает или создает HTTP клиент для сервера.

        Args:
            config: Конфигурация сервера

        Returns:
            HTTP клиент
        """
        if config.name not in self._clients:
            self._clients[config.name] = TargetServerHTTPClient(config)
        return self._clients[config.name]

    async def process_message(self, topic: str, payload: bytes) -> None:
        """
        Обрабатывает сообщение от MQTT брокера.

        Args:
            topic: MQTT топик
            payload: Данные сообщения
        """
        try:
            # Парсим сообщение
            message = self.parser.parse(topic, payload)
            logger.debug(
                f"Получено сообщение: type={message.message_type}, "
                f"from={message.from_node}, topic={topic}"
            )

            # Проверяем, нужно ли обрабатывать это сообщение
            if not message.message_type:
                logger.debug("Пропущено сообщение без типа")
                return

            # Получаем серверы для этого типа сообщений
            servers = self.repository.get_servers_for_message_type(
                message.message_type
            )

            if not servers:
                logger.debug(
                    f"Нет серверов для типа сообщения: {message.message_type}"
                )
                return

            # Трансформируем сообщение
            transformed_data = self.transformer.transform(
                message, impedance_key=self.default_impedance_key
            )

            if not transformed_data:
                logger.debug("Трансформация вернула None, пропускаем")
                return

            # Отправляем на все подходящие серверы
            await self._send_to_servers(servers, transformed_data)

        except Exception as e:
            logger.error(
                f"Ошибка обработки сообщения из топика {topic}: {e}",
                exc_info=True
            )

    async def _send_to_servers(
        self,
        servers: List[TargetServerConfig],
        data: Dict[str, Any],
    ) -> None:
        """
        Отправляет данные на список серверов.

        Args:
            servers: Список конфигураций серверов
            data: Данные для отправки
        """
        tasks = []
        for server_config in servers:
            # Создаем копию данных для каждого сервера
            # чтобы можно было использовать разные ключи импедантности
            server_data = data.copy()
            
            # Используем ключ импедантности из конфигурации сервера, если есть
            if server_config.impedance_key:
                server_data["impedance_key"] = server_config.impedance_key

            client = self._get_or_create_client(server_config)
            tasks.append(
                self._send_to_server(client, server_config.name, server_data)
            )

        # Отправляем параллельно
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Логируем результаты
        for i, result in enumerate(results):
            server_name = servers[i].name
            if isinstance(result, Exception):
                logger.error(
                    f"Ошибка отправки на {server_name}: {result}",
                    exc_info=True
                )
            elif result:
                logger.debug(f"Успешно отправлено на {server_name}")
            else:
                logger.warning(f"Не удалось отправить на {server_name}")

    async def _send_to_server(
        self,
        client: TargetServerHTTPClient,
        server_name: str,
        data: Dict[str, Any],
    ) -> bool:
        """
        Отправляет данные на один сервер.

        Args:
            client: HTTP клиент
            server_name: Название сервера (для логирования)
            data: Данные для отправки

        Returns:
            True, если отправка успешна
        """
        try:
            return await client.send(data)
        except Exception as e:
            logger.error(
                f"Ошибка отправки на {server_name}: {e}",
                exc_info=True
            )
            return False

    async def close_all_clients(self) -> None:
        """Закрывает все HTTP клиенты."""
        tasks = [
            client.close() for client in self._clients.values()
        ]
        await asyncio.gather(*tasks, return_exceptions=True)
        self._clients.clear()
        logger.info("Все HTTP клиенты закрыты")

