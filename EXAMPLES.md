# Примеры запросов на целевой сервер

Документ содержит примеры JSON запросов, которые отправляются на целевые серверы для различных типов сообщений Meshtastic.

## Общая структура запроса

Все запросы имеют следующую общую структуру:

```json
{
  "impedance_key": "ключ_идентификации",
  "idempotency_key": "уникальный_uuid_для_каждого_запроса",
  "request_type": "тип_сообщения",
  "request_body": {
    // Специфичные данные для типа сообщения
    // rssi, snr, hops_start, hops_limit, hops_away, sender_node
  },
  "meta": {
    "topic": "mqtt_топик",
    "received_at": "ISO_timestamp"
  },
  "sent_at": "ISO_timestamp"
}
```

## 1. TEXT (текстовое сообщение)

### Пример запроса:

```json
{
  "impedance_key": "default",
  "idempotency_key": "550e8400-e29b-41d4-a716-446655440000",
  "request_type": "text",
  "request_body": {
    "message_id": "1234567890",
    "from_node": "!12345678",
    "to_node": "!87654321",
    "timestamp": 1704067200,
    "text": "Hello, Meshtastic!",
    "rssi": -85,
    "snr": 5.5,
    "hops_start": 7,
    "hops_limit": 5,
    "hops_away": 2,
    "sender_node": "!87654321"
  },
  "meta": {
    "topic": "msh/2/json/!12345678",
    "received_at": "2024-01-01T12:00:00.000000"
  },
  "sent_at": "2024-01-01T12:00:00.123456"
}
```

### Описание полей:

- `request_body.message_id` - ID сообщения Meshtastic
- `request_body.from_node` - ID отправителя в формате `!hex`
- `request_body.to_node` - ID получателя (может быть `null` для broadcast)
- `request_body.timestamp` - Unix timestamp сообщения
- `request_body.text` - Текст сообщения
- `request_body.rssi` - RSSI (Received Signal Strength Indicator) в dBm
- `request_body.snr` - SNR (Signal-to-Noise Ratio) в dB
- `request_body.hops_start` - Начальное количество допустимых переходов
- `request_body.hops_limit` - Оставшееся количество переходов
- `request_body.hops_away` - Количество ретрансляций (hops_start - hops_limit)
- `request_body.sender_node` - ID ноды, которая ретранслировала пакет (опционально)

---

## 2. NODEINFO (информация о ноде)

### Пример запроса:

```json
{
  "impedance_key": "server1_key",
  "idempotency_key": "660e8400-e29b-41d4-a716-446655440001",
  "request_type": "nodeinfo",
  "request_body": {
    "message_id": "9876543210",
    "from_node": "!12345678",
    "to_node": null,
    "timestamp": 1704067200,
    "rssi": -75,
    "snr": 7.2,
    "hops_start": 7,
    "hops_limit": 6,
    "hops_away": 1,
    "sender_node": "!87654321",
    "id": "!12345678",
    "long_name": "My Meshtastic Node",
    "short_name": "MESH",
    "macaddr": "aabbccddeeff",
    "hw_model": "TBEAM",
    "is_licensed": false,
    "role": "ROUTER",
    "software_version": "2.4.0",
    "hardware_version": "1.0"
  },
  "meta": {
    "topic": "msh/2/e/!12345678",
    "received_at": "2024-01-01T12:00:00.000000"
  },
  "sent_at": "2024-01-01T12:00:00.234567"
}
```

### Описание полей:

- `request_body.id` - ID ноды
- `request_body.long_name` - Полное имя ноды
- `request_body.short_name` - Короткое имя ноды (до 4 символов)
- `request_body.macaddr` - MAC адрес устройства
- `request_body.hw_model` - Модель оборудования (TBEAM, HELTEC, etc.)
- `request_body.is_licensed` - Лицензирована ли нода
- `request_body.role` - Роль ноды (ROUTER, CLIENT, etc.)
- `request_body.software_version` - Версия прошивки
- `request_body.hardware_version` - Версия железа

**Примечание:** Структура `request_body` для nodeinfo содержит все поля из protobuf структуры `User`, поэтому могут присутствовать дополнительные поля в зависимости от версии протокола.

---

## 3. POSITION (данные о местоположении)

### Пример запроса:

```json
{
  "impedance_key": "default",
  "idempotency_key": "770e8400-e29b-41d4-a716-446655440002",
  "request_type": "position",
  "request_body": {
    "message_id": "5555555555",
    "from_node": "!12345678",
    "to_node": null,
    "timestamp": 1704067200,
    "rssi": -80,
    "snr": 6.0,
    "hops_start": 7,
    "hops_limit": 4,
    "hops_away": 3,
    "sender_node": "!87654321",
    "latitude_i": 555555555,
    "longitude_i": 333333333,
    "altitude": 150,
    "time": 1704067200,
    "location_source": "LOC_MANUAL",
    "precision_bits": 32,
    "altitude_precision": 3,
    "ground_track": 180,
    "ground_speed": 50,
    "gps_accuracy": 5
  },
  "meta": {
    "topic": "msh/2/e/!12345678",
    "received_at": "2024-01-01T12:00:00.000000"
  },
  "sent_at": "2024-01-01T12:00:00.345678"
}
```

### Описание полей:

- `request_body.latitude_i` - Широта в формате integer (делить на 1e7 для получения градусов)
- `request_body.longitude_i` - Долгота в формате integer (делить на 1e7 для получения градусов)
- `request_body.altitude` - Высота над уровнем моря в метрах
- `request_body.time` - Время получения GPS координат (Unix timestamp)
- `request_body.location_source` - Источник координат (LOC_MANUAL, LOC_AUTO, etc.)
- `request_body.precision_bits` - Точность координат в битах
- `request_body.altitude_precision` - Точность высоты
- `request_body.ground_track` - Направление движения в градусах (0-360)
- `request_body.ground_speed` - Скорость движения в м/с
- `request_body.gps_accuracy` - Точность GPS в метрах

### Пример вычисления координат:

```python
latitude = request_body["latitude_i"] / 1e7  # 55.5555555
longitude = request_body["longitude_i"] / 1e7  # 33.3333333
```

---

## 4. TELEMETRY (телеметрия)

### Пример запроса (Device Metrics):

```json
{
  "impedance_key": "default",
  "idempotency_key": "880e8400-e29b-41d4-a716-446655440003",
  "request_type": "telemetry",
  "request_body": {
    "message_id": "7777777777",
    "from_node": "!12345678",
    "to_node": null,
    "timestamp": 1704067200,
    "rssi": -82,
    "snr": 5.8,
    "hops_start": 7,
    "hops_limit": 5,
    "hops_away": 2,
    "sender_node": "!87654321",
    "device_metrics": {
      "battery_level": 85,
      "voltage": 4.2,
      "channel_utilization": 15.5,
      "air_util_tx": 10.2,
      "uptime_seconds": 86400,
      "temperature": 25.5
    }
  },
  "meta": {
    "topic": "msh/2/e/!12345678",
    "received_at": "2024-01-01T12:00:00.000000"
  },
  "sent_at": "2024-01-01T12:00:00.456789"
}
```

### Пример запроса (Environment Metrics):

```json
{
  "impedance_key": "default",
  "idempotency_key": "990e8400-e29b-41d4-a716-446655440004",
  "request_type": "telemetry",
  "request_body": {
    "message_id": "8888888888",
    "from_node": "!12345678",
    "to_node": null,
    "timestamp": 1704067200,
    "rssi": -78,
    "snr": 6.5,
    "hops_start": 7,
    "hops_limit": 6,
    "hops_away": 1,
    "sender_node": "!87654321",
    "environment_metrics": {
      "temperature": 22.5,
      "relative_humidity": 65.0,
      "barometric_pressure": 1013.25,
      "gas_resistance": 50000.0,
      "voltage": 3.3,
      "current": 0.15
    }
  },
  "meta": {
    "topic": "msh/2/e/!12345678",
    "received_at": "2024-01-01T12:00:00.000000"
  },
  "sent_at": "2024-01-01T12:00:00.567890"
}
```

### Пример запроса (Power Metrics):

```json
{
  "impedance_key": "default",
  "idempotency_key": "aa0e8400-e29b-41d4-a716-446655440005",
  "request_type": "telemetry",
  "request_body": {
    "message_id": "9999999999",
    "from_node": "!12345678",
    "to_node": null,
    "timestamp": 1704067200,
    "rssi": -83,
    "snr": 5.9,
    "hops_start": 7,
    "hops_limit": 5,
    "hops_away": 2,
    "sender_node": "!87654321",
    "power_metrics": {
      "ch1_voltage": 4.2,
      "ch1_current": 0.5,
      "ch2_voltage": 0.0,
      "ch2_current": 0.0,
      "ch3_voltage": 0.0,
      "ch3_current": 0.0
    }
  },
  "meta": {
    "topic": "msh/2/e/!12345678",
    "received_at": "2024-01-01T12:00:00.000000"
  },
  "sent_at": "2024-01-01T12:00:00.678901"
}
```

### Описание полей:

Телеметрия может содержать различные типы метрик:

- **device_metrics** - метрики устройства:
  - `battery_level` - Уровень батареи в процентах
  - `voltage` - Напряжение в вольтах
  - `channel_utilization` - Использование канала в процентах
  - `air_util_tx` - Использование эфира для передачи
  - `uptime_seconds` - Время работы в секундах
  - `temperature` - Температура устройства

- **environment_metrics** - метрики окружающей среды:
  - `temperature` - Температура в градусах Цельсия
  - `relative_humidity` - Относительная влажность в процентах
  - `barometric_pressure` - Атмосферное давление в гПа
  - `gas_resistance` - Сопротивление газового датчика
  - `voltage` - Напряжение датчика
  - `current` - Ток датчика

- **power_metrics** - метрики питания:
  - `ch1_voltage`, `ch2_voltage`, `ch3_voltage` - Напряжение на каналах
  - `ch1_current`, `ch2_current`, `ch3_current` - Ток на каналах

**Примечание:** Структура `request_body` для telemetry зависит от типа телеметрии и может содержать один или несколько блоков метрик.

---

## HTTP запрос

Все запросы отправляются методом **POST** на URL, указанный в конфигурации целевого сервера:

```
POST http://host:port/path
Content-Type: application/json
```

### Пример с использованием curl:

```bash
curl -X POST http://localhost:8080/api/meshtastic \
  -H "Content-Type: application/json" \
  -d '{
    "impedance_key": "default",
    "request_type": "text",
    "request_body": {
      "message_id": "1234567890",
      "from_node": "!12345678",
      "to_node": "!87654321",
      "timestamp": 1704067200,
      "text": "Hello, Meshtastic!"
    },
    "meta": {
      "topic": "msh/2/json/!12345678",
      "received_at": "2024-01-01T12:00:00.000000",
      "rssi": -85,
      "snr": 5.5
    },
    "sent_at": "2024-01-01T12:00:00.123456"
  }'
```

### Ожидаемые HTTP статусы ответа:

- `200 OK` - Запрос успешно обработан
- `201 Created` - Запрос успешно обработан и ресурс создан
- `202 Accepted` - Запрос принят к обработке
- `400 Bad Request` - Некорректный запрос
- `500 Internal Server Error` - Ошибка сервера

---

## Примечания

1. **Ключ идемпотентности** (`idempotency_key`) - уникальный UUID для каждого запроса, генерируется автоматически. При повторных попытках отправки (retry) используется тот же ключ, что позволяет серверу определить дубликаты запросов.

2. **Ключ импедантности** может быть переопределен для каждого целевого сервера в конфигурации `targetServers.yaml` через поле `impedance_key`.

2. **Поля `rssi` и `snr`** находятся в `request_body`, а не в `meta`. Они могут отсутствовать, если не были переданы в исходном сообщении Meshtastic.

3. **Поле `to_node`** может быть `null` для broadcast сообщений или когда получатель не указан.

4. **Поля `hops_start`, `hops_limit`, `hops_away`**:
   - `hops_start` - начальное количество допустимых переходов
   - `hops_limit` - оставшееся количество переходов
   - `hops_away` - количество ретрансляций, вычисляется как `hops_start - hops_limit`
   - Для protobuf: `hops_away` вычисляется автоматически, если не указан явно
   - Для JSON: `hops_away` может быть указан напрямую в сообщении

5. **Поле `sender_node`** (опционально) - ID ноды, которая ретранслировала пакет:
   - В protobuf сообщениях это поле `relay_node` из пакета
   - В JSON сообщениях это поле `sender`
   - Может отсутствовать, если сообщение не было ретранслировано

6. **Структура `request_body`** для типов `nodeinfo`, `position` и `telemetry` напрямую зависит от структуры protobuf сообщений Meshtastic и может содержать дополнительные поля в зависимости от версии протокола.

7. **Временные метки** (`timestamp`, `received_at`, `sent_at`) используют формат Unix timestamp (целое число) или ISO 8601 (строка) в зависимости от поля.

8. **Механизм повторных попыток (retry)**:
   - При статусе 500 или отсутствии ответа сервера запрос повторяется с тем же `idempotency_key`
   - Количество попыток и задержки настраиваются в конфигурации сервера
   - Параллельная отправка на разные серверы не блокируется - каждый сервер обрабатывается независимо

