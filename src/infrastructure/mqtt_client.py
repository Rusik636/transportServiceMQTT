"""
MQTT клиент для подключения к брокеру.

Управляет подключением и подпиской на топики.
"""

import logging
from typing import Optional, Callable, Awaitable

from aiomqtt import Client as MQTTClient
from aiomqtt.exceptions import MqttError

from src.config import MQTTBrokerConfig

logger = logging.getLogger(__name__)


class MQTTClientManager:
    """Менеджер MQTT клиента."""

    def __init__(self, config: MQTTBrokerConfig):
        """
        Создает менеджер MQTT клиента.

        Args:
            config: Конфигурация MQTT брокера
        """
        self.config = config
        self._client: Optional[MQTTClient] = None
        self._connected = False

    @property
    def is_connected(self) -> bool:
        """Проверяет, подключен ли клиент."""
        return self._connected and self._client is not None

    async def connect(self) -> None:
        """Подключается к MQTT брокеру."""
        if self._connected:
            logger.warning("MQTT клиент уже подключен")
            return

        try:
            logger.info(
                f"Подключение к MQTT брокеру: "
                f"host={self.config.host}, port={self.config.port}, "
                f"client_id={self.config.client_id}"
            )

            self._client = MQTTClient(
                hostname=self.config.host,
                port=self.config.port,
                username=self.config.username,
                password=self.config.password,
                identifier=self.config.client_id,
                keepalive=self.config.keepalive,
            )

            await self._client.__aenter__()
            self._connected = True

            logger.info("Успешно подключен к MQTT брокеру")
        except MqttError as e:
            logger.error(f"Ошибка подключения к MQTT брокеру: {e}", exc_info=True)
            self._client = None
            self._connected = False
            raise

    async def subscribe(
        self,
        topic: str,
        callback: Callable[[str, bytes], Awaitable[None]],
    ) -> None:
        """
        Подписывается на топик и устанавливает обработчик сообщений.

        Args:
            topic: MQTT топик для подписки
            callback: Асинхронная функция-обработчик (topic, payload)
        """
        if not self._client:
            raise RuntimeError("MQTT клиент не подключен")

        await self._client.subscribe(topic, qos=self.config.qos)
        logger.info(f"Подписан на топик: {topic}")

        # Обрабатываем сообщения в цикле
        async for message in self._client.messages:
            try:
                await callback(message.topic.value, message.payload)
            except Exception as e:
                logger.error(
                    f"Ошибка обработки сообщения: {e}",
                    exc_info=True
                )

    async def disconnect(self) -> None:
        """Отключается от MQTT брокера."""
        if not self._client:
            return

        try:
            await self._client.__aexit__(None, None, None)
            logger.info("Отключен от MQTT брокера")
        except Exception as e:
            logger.error(
                f"Ошибка при отключении от MQTT брокера: {e}",
                exc_info=True
            )
        finally:
            self._client = None
            self._connected = False

