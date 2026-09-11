# Telemetry Hub

Reads binary telemetry packets from a serial device, parses them, stores
them in PostgreSQL and streams them live over WebSocket.

## Status

Work in progress. See stages in commit history

## Decisions

<!-- one line per non-obvious decision, added as the project grows -->
- **XOR checksum, not CRC-16.** Enough for a learning protocol; catches
  single-byte errors; one pass. Production would use CRC-16/CCITT.
- **Big-endian.** Network byte order; matches most device protocols.
- **Resync drops one byte on bad packet**, not the whole packet, because
  the length field itself may be corrupted.


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

