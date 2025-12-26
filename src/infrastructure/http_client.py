"""
HTTP клиент для отправки данных на целевые серверы.

Использует aiohttp для асинхронной отправки данных.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
import aiohttp

from src.config import TargetServerConfig
from src.domain.interfaces import ITargetServerClient

logger = logging.getLogger(__name__)


class TargetServerHTTPClient(ITargetServerClient):
    """HTTP клиент для отправки данных на целевой сервер."""

    def __init__(self, config: TargetServerConfig):
        """
        Создает HTTP клиент.

        Args:
            config: Конфигурация целевого сервера
        """
        self.config = config
        self._session: Optional[aiohttp.ClientSession] = None
        self._base_url = f"http://{config.host}:{config.port}{config.path}"

    async def _ensure_session(self) -> None:
        """Обеспечивает наличие активной сессии."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)

    async def send(self, data: Dict[str, Any]) -> bool:
        """
        Отправляет данные на целевой сервер с повторными попытками.

        Args:
            data: Данные для отправки (должен содержать idempotency_key)

        Returns:
            True, если отправка успешна, False в противном случае
        """
        idempotency_key = data.get("idempotency_key")
        if not idempotency_key:
            logger.warning(
                f"Отсутствует idempotency_key в данных для {self.config.name}"
            )

        if not self.config.retry_enabled:
            return await self._send_once(data)

        max_attempts = self.config.retry_max_attempts
        delay = self.config.retry_delay
        backoff = self.config.retry_backoff

        for attempt in range(1, max_attempts + 1):
            success = await self._send_once(data)
            
            if success:
                if attempt > 1:
                    logger.info(
                        f"Успешно отправлено на {self.config.name} "
                        f"с попытки {attempt}/{max_attempts}, "
                        f"idempotency_key={idempotency_key}"
                    )
                return True

            # Если это не последняя попытка, ждем перед повтором
            if attempt < max_attempts:
                wait_time = delay * (backoff ** (attempt - 1))
                logger.warning(
                    f"Попытка {attempt}/{max_attempts} не удалась для "
                    f"{self.config.name}, повтор через {wait_time:.2f}с, "
                    f"idempotency_key={idempotency_key}"
                )
                await asyncio.sleep(wait_time)
            else:
                logger.error(
                    f"Все {max_attempts} попыток отправки на {self.config.name} "
                    f"не удались, idempotency_key={idempotency_key}"
                )

        return False

    async def _send_once(self, data: Dict[str, Any]) -> bool:
        """
        Отправляет данные на целевой сервер один раз.

        Args:
            data: Данные для отправки

        Returns:
            True, если отправка успешна, False в противном случае
        """
        await self._ensure_session()

        idempotency_key = data.get("idempotency_key", "unknown")

        try:
            # Добавляем заголовок с ключом идемпотентности
            headers = {
                "Content-Type": "application/json",
                "Idempotency-Key": idempotency_key,
            }

            async with self._session.post(
                self._base_url,
                json=data,
                headers=headers,
            ) as response:
                if response.status in (200, 201, 202):
                    logger.debug(
                        f"Успешно отправлено на {self.config.name}: "
                        f"status={response.status}, "
                        f"idempotency_key={idempotency_key}"
                    )
                    return True
                elif response.status == 500:
                    # 500 - внутренняя ошибка сервера, нужно повторить
                    text = await response.text()
                    logger.warning(
                        f"Ошибка 500 от {self.config.name}: {text}, "
                        f"idempotency_key={idempotency_key}"
                    )
                    return False
                else:
                    # Другие ошибки (4xx) - не повторяем
                    text = await response.text()
                    logger.warning(
                        f"Ошибка отправки на {self.config.name}: "
                        f"status={response.status}, response={text}, "
                        f"idempotency_key={idempotency_key}"
                    )
                    return False
        except aiohttp.ClientError as e:
            logger.error(
                f"Ошибка соединения с {self.config.name}: {e}, "
                f"idempotency_key={idempotency_key}",
                exc_info=True
            )
            return False
        except asyncio.TimeoutError:
            logger.error(
                f"Таймаут при отправке на {self.config.name}, "
                f"idempotency_key={idempotency_key}"
            )
            return False
        except Exception as e:
            logger.error(
                f"Неожиданная ошибка при отправке на {self.config.name}: {e}, "
                f"idempotency_key={idempotency_key}",
                exc_info=True
            )
            return False

    async def close(self) -> None:
        """Закрывает HTTP сессию."""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.debug(f"Закрыта сессия для {self.config.name}")

