"""
Конфигурация приложения.

Загружает настройки из переменных окружения и YAML файлов.
"""

import os
import logging
from pathlib import Path
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import yaml


def setup_logging(level: Optional[str] = None) -> None:
    """Настраивает логирование."""
    log_level = level or os.getenv("LOG_LEVEL", "INFO").upper()
    numeric_level = getattr(logging, log_level, logging.INFO)

    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        handlers=[logging.StreamHandler()],
        force=True,
    )


class MQTTBrokerConfig(BaseSettings):
    """Конфигурация MQTT брокера."""

    model_config = SettingsConfigDict(env_prefix="MQTT_")

    host: str = Field(default="localhost", description="Хост MQTT брокера")
    port: int = Field(default=1883, description="Порт MQTT брокера")
    username: Optional[str] = Field(default=None, description="Имя пользователя")
    password: Optional[str] = Field(default=None, description="Пароль")
    topic: str = Field(default="msh/#", description="Топик для подписки")
    client_id: str = Field(
        default="transport-service-mqtt",
        description="MQTT client ID"
    )
    keepalive: int = Field(default=60, description="Keepalive интервал в секундах")
    qos: int = Field(default=1, description="QoS уровень подписки")
    payload_format: str = Field(
        default="both",
        description="Формат сообщений: json | protobuf | both"
    )

    @field_validator("qos")
    @classmethod
    def validate_qos(cls, v: int) -> int:
        """Валидация QoS."""
        if v not in (0, 1, 2):
            raise ValueError("QoS должен быть 0, 1 или 2")
        return v

    @field_validator("payload_format")
    @classmethod
    def validate_payload_format(cls, v: str) -> str:
        """Валидация формата payload."""
        allowed = {"json", "protobuf", "both"}
        value = v.lower().strip()
        if value not in allowed:
            raise ValueError(f"payload_format должен быть одним из {allowed}")
        return value


class TargetServerConfig(BaseSettings):
    """Конфигурация целевого сервера."""

    name: str = Field(description="Название сервера")
    host: str = Field(description="IP адрес или домен")
    port: int = Field(description="Порт сервера")
    allowed_types: List[str] = Field(
        description="Список разрешенных типов сообщений"
    )
    enable: bool = Field(default=True, description="Включен ли сервер")
    impedance_key: Optional[str] = Field(
        default=None,
        description="Ключ импедантности для идентификации (опционально)"
    )
    path: str = Field(
        default="/api/meshtastic",
        description="Путь API на целевом сервере"
    )
    timeout: int = Field(
        default=10,
        description="Таймаут запроса в секундах"
    )
    retry_enabled: bool = Field(
        default=True,
        description="Включить повторные попытки при ошибках"
    )
    retry_max_attempts: int = Field(
        default=3,
        description="Максимальное количество попыток отправки"
    )
    retry_delay: float = Field(
        default=1.0,
        description="Задержка между попытками в секундах"
    )
    retry_backoff: float = Field(
        default=2.0,
        description="Множитель для экспоненциальной задержки"
    )

    @field_validator("allowed_types")
    @classmethod
    def validate_allowed_types(cls, v: List[str]) -> List[str]:
        """Валидация типов сообщений."""
        allowed = {"text", "nodeinfo", "position", "telemetry"}
        normalized = [t.lower().strip() for t in v]
        invalid = [t for t in normalized if t not in allowed]
        if invalid:
            raise ValueError(
                f"Недопустимые типы сообщений: {invalid}. "
                f"Разрешенные: {allowed}"
            )
        return normalized


class AppConfig(BaseSettings):
    """Основная конфигурация приложения."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    mqtt: MQTTBrokerConfig = Field(default_factory=MQTTBrokerConfig)
    log_level: str = Field(default="INFO", description="Уровень логирования")
    impedance_key: str = Field(
        default="default",
        description="Ключ импедантности по умолчанию"
    )

    target_servers: List[TargetServerConfig] = Field(
        default_factory=list,
        description="Список целевых серверов"
    )

    @classmethod
    def load_from_yaml(
        cls,
        yaml_path: Optional[str] = None
    ) -> "AppConfig":
        """
        Загружает конфигурацию из YAML файла.

        Args:
            yaml_path: Путь к YAML файлу. По умолчанию targetServers.yaml

        Returns:
            Экземпляр AppConfig
        """
        if yaml_path is None:
            yaml_path = Path("targetServers.yaml")
        else:
            yaml_path = Path(yaml_path)

        config = cls()

        if not yaml_path.exists():
            logging.warning(
                f"YAML файл {yaml_path} не найден. "
                "Используется конфигурация из переменных окружения."
            )
            return config

        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                yaml_data = yaml.safe_load(f)

            if not yaml_data:
                logging.warning(f"YAML файл {yaml_path} пуст.")
                return config

            # Загружаем целевые серверы
            if "target_servers" in yaml_data:
                servers_data = yaml_data["target_servers"]
                if isinstance(servers_data, list):
                    target_servers = []
                    for server_data in servers_data:
                        try:
                            server_config = TargetServerConfig(**server_data)
                            if server_config.enable:
                                target_servers.append(server_config)
                        except Exception as e:
                            logging.warning(
                                f"Ошибка при загрузке сервера из YAML: {e}"
                            )
                            continue

                    if target_servers:
                        config.target_servers = target_servers
                        logging.info(
                            f"Загружено {len(target_servers)} целевых серверов из YAML"
                        )

            # Загружаем MQTT конфигурацию, если есть
            if "mqtt" in yaml_data:
                mqtt_data = yaml_data["mqtt"]
                for key, value in mqtt_data.items():
                    if hasattr(config.mqtt, key):
                        setattr(config.mqtt, key, value)

            # Загружаем общие настройки
            if "impedance_key" in yaml_data:
                config.impedance_key = yaml_data["impedance_key"]

            if "log_level" in yaml_data:
                config.log_level = yaml_data["log_level"]

        except yaml.YAMLError as e:
            logging.error(f"Ошибка при парсинге YAML файла {yaml_path}: {e}")
        except Exception as e:
            logging.error(f"Ошибка при загрузке YAML файла {yaml_path}: {e}")

        return config

