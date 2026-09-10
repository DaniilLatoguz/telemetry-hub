import pytest

from telemetry.protocol import (
    MAGIC,
    ProtocolError,
    TelemetryPacket,
    checksum,
    parse,
    serialize,
)


def make_packet(**overrides) -> TelemetryPacket:
    base = dict(timestamp=1_700_000_000, temperature=42.5, voltage_mv=12_000, frame_id=7)
    base.update(overrides)
    return TelemetryPacket(**base)

def test_serialize_starts_with_magic():
    assert serialize(make_packet()).startswith(MAGIC)

def test_serialized_length():
    assert len(serialize(make_packet())) == 2 + 1 + 1 + 14 + 1

def test_roundtrip():
    pkt = make_packet()
    assert parse(serialize(pkt)) == pkt

def test_roundtrip_float_precision():
    pkt = make_packet(temperature=36.6)
    parsed = parse(serialize(pkt))
    assert parsed.temperature == pytest.approx(36.6, abs=1e-4)

def test_parse_bad_magic():
    data = b"\x00\x00" + serialize(make_packet())[2:]
    with pytest.raises(ProtocolError):
        parse(data)

def test_parse_bad_crc():
    data = bytearray(serialize(make_packet()))
    data[-1] ^= 0xFF
    with pytest.raises(ProtocolError):
        parse(bytes(data))

def test_parse_truncated():
    data = serialize(make_packet())[:-3]
    with pytest.raises(ProtocolError):
        parse(data)

def test_parse_too_short():
    with pytest.raises(ProtocolError):
        parse(b"\xaa")

def test_checksum_is_xor():
    assert checksum(b"\x01\x02\x03") == 0x01 ^ 0x02 ^ 0x03
    assert checksum(b"") == 0