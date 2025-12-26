"""
Доменные модели для Meshtastic сообщений.

Определяет структуру данных для различных типов сообщений Meshtastic.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class MeshtasticMessage(BaseModel):
    """Базовая модель сообщения от Meshtastic."""

    topic: str = Field(description="MQTT топик, из которого получено сообщение")
    raw_payload: Dict[str, Any] = Field(
        description="Исходный payload (распарсенный)"
    )
    raw_payload_bytes: Optional[bytes] = Field(
        default=None,
        description="Исходный payload в сыром виде (bytes)",
    )
    received_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Время получения сообщения"
    )
    message_id: Optional[str] = Field(default=None, description="ID сообщения")
    from_node: Optional[str] = Field(default=None, description="ID отправителя")
    to_node: Optional[str] = Field(default=None, description="ID получателя")
    message_type: Optional[str] = Field(
        default=None,
        description="Тип сообщения (text, nodeinfo, position, telemetry)"
    )
    timestamp: Optional[int] = Field(
        default=None,
        description="Unix timestamp сообщения"
    )
    rssi: Optional[int] = Field(
        default=None,
        description="RSSI (Received Signal Strength Indicator) в dBm"
    )
    snr: Optional[float] = Field(
        default=None,
        description="SNR (Signal-to-Noise Ratio) в dB"
    )
    sender_node: Optional[str] = Field(
        default=None,
        description="ID ноды, которая ретранслировала сообщение (relay_node)"
    )
    hops_start: Optional[int] = Field(
        default=None,
        description="Начальное количество допустимых переходов (hop_start)"
    )
    hops_limit: Optional[int] = Field(
        default=None,
        description="Оставшееся количество переходов (hop_limit)"
    )
    hops_away: Optional[int] = Field(
        default=None,
        description="Количество ретрансляций (hops_away = hops_start - hops_limit)"
    )


class MessageType:
    """Константы типов сообщений Meshtastic."""

    TEXT = "text"
    NODEINFO = "nodeinfo"
    POSITION = "position"
    TELEMETRY = "telemetry"

    @classmethod
    def is_valid(cls, message_type: Optional[str]) -> bool:
        """Проверяет, является ли тип сообщения валидным."""
        if not message_type:
            return False
        return message_type.lower() in {
            cls.TEXT,
            cls.NODEINFO,
            cls.POSITION,
            cls.TELEMETRY,
        }

