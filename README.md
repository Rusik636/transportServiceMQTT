# Transport Service MQTT

Микросервис для получения данных от Meshtastic MQTT брокера и отправки их на целевые серверы.

## Описание

Сервис подключается к MQTT брокеру, получает сообщения от Meshtastic устройств в форматах Protobuf и JSON, парсит их и отправляет на настроенные целевые серверы через HTTP API.

## Архитектура

Проект следует принципам слоистой архитектуры и SOLID:

- **Domain** - доменные модели и интерфейсы
- **DTO** - объекты передачи данных
- **Application** - бизнес-логика и сервисы
- **Infrastructure** - внешние зависимости (MQTT, HTTP, парсеры)

## Поддерживаемые типы сообщений

- `text` - текстовые сообщения
- `nodeinfo` - информация о нодах
- `position` - данные о местоположении
- `telemetry` - телеметрия

## Установка

1. Клонируйте репозиторий
2. Установите зависимости:

```bash
pip install -r requirements.txt
```

3. Настройте конфигурацию:

```bash
cp .env.example .env
# Отредактируйте .env файл
```

4. Настройте целевые серверы в `targetServers.yaml`

## Конфигурация

### Переменные окружения (.env)

```env
MQTT_HOST=localhost
MQTT_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=
MQTT_TOPIC=msh/#
MQTT_CLIENT_ID=transport-service-mqtt
MQTT_KEEPALIVE=60
MQTT_QOS=1
MQTT_PAYLOAD_FORMAT=both

IMPEDANCE_KEY=default
LOG_LEVEL=INFO
```

### Файл targetServers.yaml

```yaml
target_servers:
  - name: server1
    host: localhost
    port: 8080
    allowed_types:
      - text
      - nodeinfo
      - position
      - telemetry
    enable: true
    impedance_key: server1_key
    path: /api/meshtastic
    timeout: 10
    retry_enabled: true
    retry_max_attempts: 3
    retry_delay: 1.0
    retry_backoff: 2.0
```

## Запуск

```bash
python main.py
```

## Структура данных

### Формат отправляемых данных на целевой сервер

Все запросы отправляются методом POST с JSON телом. Подробные примеры для каждого типа сообщения см. в файле [EXAMPLES.md](EXAMPLES.md).

### Ключ идемпотентности

Каждый запрос автоматически получает уникальный ключ идемпотентности (`idempotency_key`) в формате UUID. Этот ключ:
- Генерируется автоматически для каждого нового запроса
- Сохраняется при повторных попытках отправки (retry)
- Передается в HTTP заголовке `Idempotency-Key`
- Позволяет серверу определить дубликаты запросов

### Механизм повторных попыток (Retry)

При ошибках отправки (статус 500 или отсутствие ответа) запрос автоматически повторяется:
- Количество попыток настраивается через `retry_max_attempts` (по умолчанию 3)
- Используется экспоненциальная задержка: `delay * (backoff ^ (attempt - 1))`
- При каждой попытке используется тот же `idempotency_key`
- Параллельная отправка на разные серверы не блокируется - каждый сервер обрабатывается независимо
- Если один сервер отвечает 500 или не отвечает, другие серверы продолжают получать запросы параллельно

**Общая структура:**

```json
{
  "impedance_key": "ключ_идентификации",
  "request_type": "text|nodeinfo|position|telemetry",
  "request_body": {
    // Специфичные данные для типа сообщения
  },
  "meta": {
    "topic": "mqtt_топик",
    "received_at": "ISO_timestamp",
    "rssi": -85,
    "snr": 5.5
  },
  "sent_at": "ISO_timestamp"
}
```

**Краткие примеры:**

- **TEXT**: `request_body` содержит `message_id`, `from_node`, `to_node`, `timestamp`, `text`
- **NODEINFO**: `request_body` содержит информацию о ноде (id, long_name, short_name, hw_model, etc.)
- **POSITION**: `request_body` содержит координаты (latitude_i, longitude_i, altitude, etc.)
- **TELEMETRY**: `request_body` содержит метрики (device_metrics, environment_metrics, power_metrics)

Подробные примеры см. в [EXAMPLES.md](EXAMPLES.md).

## Разработка

### Структура проекта

```
transportServiceMQTT/
├── src/
│   ├── domain/          # Доменные модели и интерфейсы
│   ├── DTO/             # Объекты передачи данных
│   ├── application/     # Бизнес-логика
│   ├── infrastructure/  # Внешние зависимости
│   └── config.py        # Конфигурация
├── main.py              # Точка входа
├── targetServers.yaml   # Конфигурация целевых серверов
├── requirements.txt     # Зависимости
└── README.md           # Документация
```

### Принципы проектирования

- **Separation of Concerns** - разделение ответственности между слоями
- **Dependency Injection** - внедрение зависимостей через конструкторы
- **Interface Segregation** - использование интерфейсов для абстракций
- **Single Responsibility** - каждый класс имеет одну ответственность

## Безопасность

- Не храните секреты в репозитории
- Используйте переменные окружения для конфиденциальных данных
- Валидация всех входящих данных через Pydantic
- Безопасная обработка ошибок без раскрытия внутренней информации

## Логирование

Логирование настроено через стандартный модуль `logging` Python. Уровень логирования настраивается через переменную окружения `LOG_LEVEL` или в `targetServers.yaml`.

## Лицензия

[Укажите лицензию]

