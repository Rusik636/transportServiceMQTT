"""
Парсеры сообщений Meshtastic.

Парсит protobuf и JSON сообщения от Meshtastic брокера.
"""

import base64
import json
import logging
from typing import Dict, Any, Optional

try:
    from google.protobuf.json_format import MessageToDict
    from meshtastic.protobuf import mqtt_pb2, mesh_pb2, telemetry_pb2

    PROTOBUF_AVAILABLE = True
except ImportError:
    PROTOBUF_AVAILABLE = False

from src.domain.models import MeshtasticMessage
from src.domain.interfaces import IMessageParser

logger = logging.getLogger(__name__)


def _normalize_node_id(node_id: Any) -> Optional[str]:
    """
    Нормализует node ID к единому формату "!hex".

    Args:
        node_id: Node ID в любом формате

    Returns:
        Нормализованный node ID или None
    """
    if node_id is None:
        return None

    try:
        if isinstance(node_id, int):
            return f"!{hex(node_id)[2:]}"
        elif isinstance(node_id, str):
            node_str = node_id.strip()
            if not node_str:
                return None

            if node_str.startswith("!"):
                hex_part = node_str[1:]
                if not hex_part:
                    return None
                try:
                    int(hex_part, 16)
                    return f"!{hex_part.lower()}"
                except ValueError:
                    return f"!{hex_part.lower()}"

            if node_str.startswith(("0x", "0X")):
                hex_part = node_str[2:]
                if not hex_part:
                    return None
                try:
                    num = int(hex_part, 16)
                    return f"!{hex(num)[2:]}"
                except ValueError:
                    return f"!{hex_part.lower()}"

            try:
                num = int(node_str, 16)
                return f"!{hex(num)[2:]}"
            except ValueError:
                try:
                    num = int(node_str, 10)
                    return f"!{hex(num)[2:]}"
                except ValueError:
                    return f"!{node_str.lower()}"
        else:
            return _normalize_node_id(str(node_id))
    except Exception as e:
        logger.warning(f"Ошибка нормализации node_id: {node_id}, error: {e}")
        return None


class JsonMessageParser(IMessageParser):
    """Парсер JSON сообщений от Meshtastic."""

    def parse(self, topic: str, payload: bytes) -> MeshtasticMessage:
        """
        Парсит JSON payload.

        Args:
            topic: MQTT топик
            payload: Данные в байтах

        Returns:
            MeshtasticMessage
        """
        payload_str = payload.decode("utf-8", errors="replace")
        raw_payload: Dict[str, Any] = json.loads(payload_str)

        return self._create_message(raw_payload, topic, payload)

    def _create_message(
        self,
        raw_payload: Dict[str, Any],
        topic: str,
        raw_payload_bytes: bytes,
    ) -> MeshtasticMessage:
        """Создает MeshtasticMessage из распарсенных данных."""
        message_type = raw_payload.get("type")
        message_id = raw_payload.get("id")
        from_node = raw_payload.get("from")
        sender_node = raw_payload.get("sender")
        to_node = raw_payload.get("to")
        hop_start = raw_payload.get("hop_start")
        hop_limit = raw_payload.get("hop_limit")
        hops_away = raw_payload.get("hops_away")
        timestamp = raw_payload.get("rx_time") or raw_payload.get("timestamp")
        rssi = raw_payload.get("rssi")
        snr = raw_payload.get("snr")

        from_node_str = _normalize_node_id(from_node)
        sender_node_str = _normalize_node_id(sender_node)
        to_node_str = _normalize_node_id(to_node)

        # Для JSON hops_away может быть напрямую указан
        hops_away_int = None
        if hops_away is not None:
            try:
                hops_away_int = int(hops_away)
            except (ValueError, TypeError):
                hops_away_int = None

        return MeshtasticMessage(
            topic=topic,
            raw_payload=raw_payload,
            raw_payload_bytes=raw_payload_bytes,
            message_id=str(message_id) if message_id else None,
            from_node=from_node_str,
            sender_node=sender_node_str,
            to_node=to_node_str,
            message_type=message_type,
            timestamp=timestamp,
            rssi=int(rssi) if rssi is not None else None,
            snr=float(snr) if snr is not None else None,
            hops_start=int(hop_start) if hop_start is not None else None,
            hops_limit=int(hop_limit) if hop_limit is not None else None,
            hops_away=hops_away_int,
        )


class ProtobufMessageParser(IMessageParser):
    """Парсер Protobuf сообщений от Meshtastic."""

    def parse(self, topic: str, payload: bytes) -> MeshtasticMessage:
        """
        Парсит Protobuf payload.

        Args:
            topic: MQTT топик
            payload: Данные в байтах

        Returns:
            MeshtasticMessage
        """
        if not PROTOBUF_AVAILABLE:
            raise RuntimeError(
                "Protobuf парсинг недоступен. "
                "Установите зависимости: meshtastic, protobuf"
            )

        raw_payload = self._parse_protobuf_payload(payload)
        return self._create_message(raw_payload, topic, payload)

    def _parse_protobuf_payload(self, payload: bytes) -> Dict[str, Any]:
        """Парсит protobuf payload в словарь."""
        envelope = mqtt_pb2.ServiceEnvelope()
        envelope.ParseFromString(payload)

        envelope_dict = MessageToDict(
            envelope,
            preserving_proto_field_name=True,
        )

        packet = (
            envelope_dict.get("packet", {})
            if isinstance(envelope_dict, dict)
            else {}
        )
        decoded = packet.get("decoded", {}) if isinstance(packet, dict) else {}

        raw_payload: Dict[str, Any] = {
            "type": None,
            "portnum": decoded.get("portnum"),
            "id": packet.get("id"),
            "from": packet.get("from"),
            "sender": packet.get("relay_node"),  # relay_node в protobuf
            "to": packet.get("to"),
            "hop_start": packet.get("hop_start"),
            "hop_limit": packet.get("hop_limit"),
            "timestamp": packet.get("rx_time") or packet.get("timestamp"),
            "rx_time": packet.get("rx_time"),
            "rssi": packet.get("rx_rssi"),
            "snr": packet.get("rx_snr"),
            "payload": {},
        }

        portnum = decoded.get("portnum")
        if portnum:
            portnum_lower = str(portnum).lower()
            if "text_message_compressed" in portnum_lower:
                raw_payload["type"] = "text"
            elif "text_message" in portnum_lower:
                raw_payload["type"] = "text"
            elif "nodeinfo" in portnum_lower:
                raw_payload["type"] = "nodeinfo"
            elif "position" in portnum_lower:
                raw_payload["type"] = "position"
            elif "telemetry" in portnum_lower:
                raw_payload["type"] = "telemetry"

        payload_b64 = decoded.get("payload")
        if payload_b64:
            try:
                decoded_bytes = base64.b64decode(payload_b64)
                raw_payload["payload"] = {
                    "raw_base64": payload_b64,
                }

                if raw_payload["type"] == "text":
                    text = decoded_bytes.decode("utf-8", errors="replace")
                    raw_payload["payload"]["text"] = text

                elif raw_payload["type"] == "nodeinfo":
                    try:
                        user_msg = mesh_pb2.User()
                        user_msg.ParseFromString(decoded_bytes)
                        raw_payload["payload"] = MessageToDict(
                            user_msg, preserving_proto_field_name=True
                        )
                    except Exception as e:
                        raw_payload["payload"] = {
                            "raw_base64": payload_b64,
                            "decode_error": str(e),
                        }

                elif raw_payload["type"] == "position":
                    try:
                        pos = mesh_pb2.Position()
                        pos.ParseFromString(decoded_bytes)
                        raw_payload["payload"] = MessageToDict(
                            pos, preserving_proto_field_name=True
                        )
                    except Exception as e:
                        raw_payload["payload"] = {
                            "raw_base64": payload_b64,
                            "decode_error": str(e),
                        }

                elif raw_payload["type"] == "telemetry":
                    try:
                        tm = telemetry_pb2.Telemetry()
                        tm.ParseFromString(decoded_bytes)
                        raw_payload["payload"] = MessageToDict(
                            tm, preserving_proto_field_name=True
                        )
                    except Exception as e:
                        raw_payload["payload"] = {
                            "raw_base64": payload_b64,
                            "decode_error": str(e),
                        }

            except Exception as e:
                logger.warning(f"Ошибка декодирования payload: {e}")
                raw_payload["payload"] = {"raw_base64": payload_b64}

        return raw_payload

    def _create_message(
        self,
        raw_payload: Dict[str, Any],
        topic: str,
        raw_payload_bytes: bytes,
    ) -> MeshtasticMessage:
        """Создает MeshtasticMessage из распарсенных данных."""
        message_type = raw_payload.get("type")
        message_id = raw_payload.get("id")
        from_node = raw_payload.get("from")
        sender_node = raw_payload.get("sender")
        to_node = raw_payload.get("to")
        hop_start = raw_payload.get("hop_start")
        hop_limit = raw_payload.get("hop_limit")
        hops_away = raw_payload.get("hops_away")
        timestamp = raw_payload.get("timestamp") or raw_payload.get("rx_time")
        rssi = raw_payload.get("rssi")
        snr = raw_payload.get("snr")

        from_node_str = _normalize_node_id(from_node)
        sender_node_str = _normalize_node_id(sender_node)
        to_node_str = _normalize_node_id(to_node)

        # Вычисляем hops_away для protobuf, если не указан
        hops_away_int = None
        if hops_away is not None:
            try:
                hops_away_int = int(hops_away)
            except (ValueError, TypeError):
                hops_away_int = None
        
        # Для protobuf: hops_away = hop_start - hop_limit
        if hops_away_int is None and hop_start is not None and hop_limit is not None:
            try:
                hs = int(hop_start)
                hl = int(hop_limit)
                diff = hs - hl
                hops_away_int = diff if diff >= 0 else None
            except (ValueError, TypeError):
                pass

        return MeshtasticMessage(
            topic=topic,
            raw_payload=raw_payload,
            raw_payload_bytes=raw_payload_bytes,
            message_id=str(message_id) if message_id else None,
            from_node=from_node_str,
            sender_node=sender_node_str,
            to_node=to_node_str,
            message_type=message_type,
            timestamp=timestamp,
            rssi=int(rssi) if rssi is not None else None,
            snr=float(snr) if snr is not None else None,
            hops_start=int(hop_start) if hop_start is not None else None,
            hops_limit=int(hop_limit) if hop_limit is not None else None,
            hops_away=hops_away_int,
        )


class MessageParserFactory:
    """Фабрика для создания парсеров сообщений."""

    @staticmethod
    def create_parser(
        payload_format: str,
    ) -> IMessageParser:
        """
        Создает парсер в зависимости от формата.

        Args:
            payload_format: Формат сообщений (json, protobuf, both)

        Returns:
            Парсер сообщений
        """
        format_lower = payload_format.lower()

        if format_lower == "json":
            return JsonMessageParser()
        elif format_lower == "protobuf":
            return ProtobufMessageParser()
        elif format_lower == "both":
            # Для "both" возвращаем парсер, который пробует оба формата
            return DualFormatParser()
        else:
            raise ValueError(f"Неподдерживаемый формат: {payload_format}")


class DualFormatParser(IMessageParser):
    """Парсер, который пробует оба формата (JSON и Protobuf)."""

    def __init__(self):
        """Инициализирует парсеры."""
        self.json_parser = JsonMessageParser()
        self.protobuf_parser = ProtobufMessageParser()

    def parse(self, topic: str, payload: bytes) -> MeshtasticMessage:
        """
        Парсит сообщение, пробуя оба формата.

        Args:
            topic: MQTT топик
            payload: Данные в байтах

        Returns:
            MeshtasticMessage
        """
        # Сначала пробуем JSON (быстрее)
        try:
            return self.json_parser.parse(topic, payload)
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass

        # Если JSON не подошел, пробуем Protobuf
        try:
            return self.protobuf_parser.parse(topic, payload)
        except Exception as e:
            logger.error(f"Ошибка парсинга сообщения: {e}")
            raise

