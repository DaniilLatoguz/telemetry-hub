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

- **Reader runs in a thread, not asyncio.** pyserial is blocking; one
  daemon thread with a timeout-based read loop is the simplest reliable
  option. asyncio enters at the API layer (stage 6).
- **Reader emits via callback, not a queue.** Keeps it independent of
  consumers; stage 6 fans out to DB queue and asyncio with one function.
- **Reconnect on SerialException** with fixed delay; stop() interrupts the
  delay via Event.wait().
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

## Benchmarks

### Timestamp index (1,000,000 rows, range query over 300 s)

| Plan       | Execution time |
|------------|----------------|
| Seq Scan   | ~120 ms        |
| Index Scan | ~0.4 ms        |

Index: B-tree on `timestamp`. Range queries are the primary access pattern.