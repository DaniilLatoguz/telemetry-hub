"""Binary packet format: serialize / parse a single packet"""

import struct
from dataclasses import dataclass

MAGIC = b"\xaa\x55"
TYPE_TELEMETRY = 0x01

PAYLOAD_FMT = ">IfHI"                       # timestamp, temperature, voltage, frame_id
PAYLOAD_LEN = struct.calcsize(PAYLOAD_FMT)  # 14
HEADER_LEN = len(MAGIC) + 2                 # magic + len + type = 4
MIN_PACKET_LEN = HEADER_LEN + 1             # header + crc, empty payload

class ProtocolError(ValueError):
    """Raised when bytes do not form a valid packet."""

@dataclass(frozen=True)
class TelemetryPacket:
    timestamp: int
    temperature: float
    voltage_mv: int
    frame_id: int

def checksum(data: bytes) -> int:
    """XOR of all bytes. Simple, catches single-byte corruption"""
    result = 0
    for b in data:
        result ^= b
    return result

def serialize(packet: TelemetryPacket) -> bytes:
    payload = struct.pack(
        PAYLOAD_FMT,
        packet.timestamp,
        packet.temperature,
        packet.voltage_mv,
        packet.frame_id,
    )
    body = bytes([len(payload), TYPE_TELEMETRY]) + payload
    return MAGIC + body + bytes([checksum(body)])

def parse(data: bytes) -> TelemetryPacket:
    """Parse exactly one packet. Raise ProtocolError on any problem.

    Steps:
    1. If len (data) < MIN_PACKET_LEN -> ProtocolError("too short")
    2. If data[:2] != MAGIC -> ProtocolError("bad magic")
    3. Length = data[2], ptype = data[3]
    4. total = HEADER_LEN + length + 1
       If len(data) < total -> ProtocolError("truncated")
    5. body = data[2 : HEADER_LEN + length]  # len + type + payload
       crc = data[HEADER_LEN + length]
       If checksum(body) != crc -> ProtocolError("bad crc")
    6. If ptype != TYPE_TELEMETRY -> ProtocolError("unsupported type")
    7. If length != PAYLOAD_LEN -> ProtocolError("bad payload length")
    8. struct.unpack(PAYLOAD_FMT, payload) -> TelemetryPacket
    """
    if len(data) < MIN_PACKET_LEN:
        raise ProtocolError("too short")
    if data[:2] != MAGIC:
        raise ProtocolError("bad magic")
    length = data[2]
    ptype = data[3]
    total = HEADER_LEN + length + 1
    if len(data) < total:
        raise ProtocolError("truncated")
    body = data[2 : HEADER_LEN + length]
    crc = data[HEADER_LEN + length]
    if checksum(body) != crc:
        raise ProtocolError("bad crc")
    if ptype != TYPE_TELEMETRY:
        raise ProtocolError("unsupported type")
    if length != PAYLOAD_LEN:
        raise ProtocolError("bad payload length")
    payload = data[HEADER_LEN : HEADER_LEN + length]
    timestamp, temperature, voltage_mv, frame_id = struct.unpack(PAYLOAD_FMT, payload)

    return TelemetryPacket(timestamp, temperature, voltage_mv, frame_id)
