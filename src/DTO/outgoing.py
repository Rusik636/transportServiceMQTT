"""
DTO для исходящих сообщений на целевые серверы.

Определяет структуру данных, отправляемых на целевые серверы.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator


class OutgoingMessageDTO(BaseModel):
    """
    DTO для отправки сообщения на целевой сервер.

    Структура:
    1. ключ импедантности (impedance_key)
    2. ключ идемпотентности (idempotency_key) - уникальный для каждого запроса
    3. тип запроса (request_type)
    4. тело запроса (request_body)
    5. метаинформация (meta)
    6. время отправки (sent_at)
    """

    impedance_key: str = Field(
        description="Ключ импедантности для идентификации источника"
    )
    idempotency_key: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Уникальный ключ идемпотентности для каждого запроса"
    )
    request_type: str = Field(
        description="Тип запроса: text, nodeinfo, position, telemetry"
    )
    request_body: Dict[str, Any] = Field(
        description="Тело запроса с данными сообщения"
    )
    meta: Dict[str, Any] = Field(
        default_factory=dict,
        description="Метаинформация о сообщении"
    )
    sent_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Время отправки сообщения"
    )

    @field_validator("idempotency_key")
    @classmethod
    def validate_idempotency_key(cls, v: str) -> str:
        """Валидация ключа идемпотентности."""
        if not v or not v.strip():
            return str(uuid.uuid4())
        return v

    def to_dict(self) -> Dict[str, Any]:
        """Преобразует DTO в словарь для сериализации."""
        return {
            "impedance_key": self.impedance_key,
            "idempotency_key": self.idempotency_key,
            "request_type": self.request_type,
            "request_body": self.request_body,
            "meta": self.meta,
            "sent_at": self.sent_at.isoformat(),
        }

