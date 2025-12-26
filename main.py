"""
Точка входа приложения Transport Service MQTT.

Микросервис для получения данных от Meshtastic MQTT брокера
и отправки их на целевые серверы.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

from src.config import AppConfig, setup_logging
from src.infrastructure.mqtt_client import MQTTClientManager
from src.infrastructure.parsers import MessageParserFactory
from src.application.transformers import MessageTransformer
from src.application.repositories import TargetServerRepository
from src.application.services import MessageProcessingService

# Добавляем src в путь для импортов
sys.path.insert(0, str(Path(__file__).parent))

logger = logging.getLogger(__name__)


class TransportServiceApp:
    """Основной класс приложения."""

    def __init__(self, config: AppConfig):
        """
        Создает приложение.

        Args:
            config: Конфигурация приложения
        """
        self.config = config
        self.mqtt_client: Optional[MQTTClientManager] = None
        self.processing_service: Optional[MessageProcessingService] = None

    async def _setup_services(self) -> None:
        """Настраивает сервисы приложения."""
        # Создаем парсер сообщений
        parser = MessageParserFactory.create_parser(
            self.config.mqtt.payload_format
        )

        # Создаем трансформатор
        transformer = MessageTransformer(
            default_impedance_key=self.config.impedance_key
        )

        # Создаем репозиторий целевых серверов
        repository = TargetServerRepository(self.config.target_servers)

        # Создаем сервис обработки сообщений
        self.processing_service = MessageProcessingService(
            parser=parser,
            transformer=transformer,
            repository=repository,
            default_impedance_key=self.config.impedance_key,
        )

        # Создаем MQTT клиент
        self.mqtt_client = MQTTClientManager(self.config.mqtt)

    async def _message_handler(self, topic: str, payload: bytes) -> None:
        """
        Обработчик сообщений от MQTT брокера.

        Args:
            topic: MQTT топик
            payload: Данные сообщения
        """
        if self.processing_service:
            await self.processing_service.process_message(topic, payload)

    async def run(self) -> None:
        """Запускает приложение."""
        try:
            logger.info("Инициализация Transport Service MQTT")

            # Настраиваем сервисы
            await self._setup_services()

            # Подключаемся к MQTT брокеру
            await self.mqtt_client.connect()

            # Подписываемся на топик
            logger.info(f"Подписка на топик: {self.config.mqtt.topic}")
            await self.mqtt_client.subscribe(
                self.config.mqtt.topic,
                self._message_handler,
            )

        except KeyboardInterrupt:
            logger.info("Получен сигнал прерывания")
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}", exc_info=True)
            raise
        finally:
            await self.cleanup()

    async def cleanup(self) -> None:
        """Очищает ресурсы приложения."""
        logger.info("Очистка ресурсов...")

        if self.processing_service:
            await self.processing_service.close_all_clients()

        if self.mqtt_client:
            await self.mqtt_client.disconnect()

        logger.info("Очистка завершена")


async def main() -> None:
    """Главная функция приложения."""
    # Настраиваем базовое логирование
    setup_logging()

    try:
        # Загружаем конфигурацию
        config = AppConfig.load_from_yaml()

        # Настраиваем полное логирование
        setup_logging(config.log_level)
        logger.info("Загружена конфигурация приложения")

        # Проверяем наличие целевых серверов
        if not config.target_servers:
            logger.warning(
                "Не найдено целевых серверов в конфигурации. "
                "Проверьте файл targetServers.yaml"
            )
        else:
            logger.info(
                f"Найдено {len(config.target_servers)} целевых серверов"
            )

        # Создаем и запускаем приложение
        app = TransportServiceApp(config)
        await app.run()

    except KeyboardInterrupt:
        logger.info("Получен сигнал прерывания")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

