# Telemetry Hub

Reads binary telemetry packets from a serial device, parses them, stores
them in PostgreSQL and streams them live over WebSocket.

## Status

Work in progress. See stages in commit history

## Decisions

<!-- one line per non-obvious decision, added as the project grows -->

## Packet format

| Field    | Size  | Type    | Notes                          |
|----------|-------|---------|--------------------------------|
| magic    | 2     | bytes   | `0xAA 0x55`, marks packet start |
| len      | 1     | uint8   | payload length                  |
| type     | 1     | uint8   | `0x01` telemetry               |
| payload  | len   | bytes   | see below                       |
| crc      | 1     | uint8   | XOR of bytes from `len` to end of payload |

### Telemetry payload (`type = 0x01`), 14 bytes, big-endian

| Field       | Type    |
|-------------|---------|
| timestamp   | uint32  |
| temperature | float32 |
| voltage_mv  | uint16  |
| frame_id    | uint32  |

