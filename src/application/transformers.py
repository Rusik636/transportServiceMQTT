"""
Трансформаторы сообщений.

Преобразуют доменные модели в DTO для отправки на целевые серверы.
"""

import logging
from typing import Dict, Any, Optional

from src.domain.models import MeshtasticMessage, MessageType
from src.domain.interfaces import IMessageTransformer
from src.DTO.outgoing import OutgoingMessageDTO

logger = logging.getLogger(__name__)


class MessageTransformer(IMessageTransformer):
    """Трансформатор сообщений Meshtastic в формат для целевых серверов."""

    def __init__(self, default_impedance_key: str = "default"):
        """
        Создает трансформатор.

        Args:
            default_impedance_key: Ключ импедантности по умолчанию
        """
        self.default_impedance_key = default_impedance_key

    def transform(
        self,
        message: MeshtasticMessage,
        impedance_key: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Трансформирует сообщение в формат для отправки.

        Args:
            message: Сообщение для трансформации
            impedance_key: Ключ импедантности (опционально)

        Returns:
            Словарь с данными для отправки или None
        """
        if not MessageType.is_valid(message.message_type):
            logger.debug(
                f"Пропущено сообщение неизвестного типа: {message.message_type}"
            )
            return None

        # Определяем ключ импедантности
        key = impedance_key or self.default_impedance_key

        # Формируем тело запроса
        request_body = self._build_request_body(message)

        # Формируем метаинформацию
        meta = self._build_meta(message)

        # Создаем DTO
        dto = OutgoingMessageDTO(
            impedance_key=key,
            request_type=message.message_type.lower(),
            request_body=request_body,
            meta=meta,
        )

        return dto.to_dict()

    def _build_request_body(self, message: MeshtasticMessage) -> Dict[str, Any]:
        """
        Формирует тело запроса из сообщения.

        Args:
            message: Сообщение Meshtastic

        Returns:
            Словарь с телом запроса
        """
        body: Dict[str, Any] = {}

        # Базовые поля
        if message.message_id:
            body["message_id"] = message.message_id
        if message.from_node:
            body["from_node"] = message.from_node
        if message.to_node:
            body["to_node"] = message.to_node
        if message.timestamp:
            body["timestamp"] = message.timestamp

        # RSSI и SNR в body
        if message.rssi is not None:
            body["rssi"] = message.rssi
        if message.snr is not None:
            body["snr"] = message.snr

        # Hops информация
        if message.hops_start is not None:
            body["hops_start"] = message.hops_start
        if message.hops_limit is not None:
            body["hops_limit"] = message.hops_limit
        if message.hops_away is not None:
            body["hops_away"] = message.hops_away

        # ID ноды, которая ретранслировала пакет (опционально)
        if message.sender_node:
            body["sender_node"] = message.sender_node

        # Специфичные поля для разных типов сообщений
        if message.message_type == MessageType.TEXT:
            payload = message.raw_payload.get("payload", {})
            if isinstance(payload, dict):
                body["text"] = payload.get("text", "")
            else:
                body["text"] = message.raw_payload.get("text", "")

        elif message.message_type == MessageType.NODEINFO:
            payload = message.raw_payload.get("payload", {})
            if isinstance(payload, dict):
                body.update(payload)

        elif message.message_type == MessageType.POSITION:
            payload = message.raw_payload.get("payload", {})
            if isinstance(payload, dict):
                body.update(payload)

        elif message.message_type == MessageType.TELEMETRY:
            payload = message.raw_payload.get("payload", {})
            if isinstance(payload, dict):
                body.update(payload)

        return body

    def _build_meta(self, message: MeshtasticMessage) -> Dict[str, Any]:
        """
        Формирует метаинформацию о сообщении.

        Args:
            message: Сообщение Meshtastic

        Returns:
            Словарь с метаинформацией
        """
        meta: Dict[str, Any] = {
            "topic": message.topic,
            "received_at": message.received_at.isoformat(),
        }

        # RSSI и SNR теперь в request_body, не в meta

        return meta

