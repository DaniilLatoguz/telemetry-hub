from telemetry.protocol import TelemetryPacket, serialize
from telemetry.stream import StreamParser


def pkt(frame_id: int) -> TelemetryPacket:
    return TelemetryPacket(timestamp=1_700_000_000,
                           temperature=40.0,
                           voltage_mv=12_000,
                           frame_id=frame_id)

def test_single_packet():
    p = StreamParser()
    assert p.feed(serialize(pkt(1))) == [pkt(1)]

def test_packet_split_in_two():
    p = StreamParser()
    data = serialize(pkt(1))
    assert p.feed(data[:7]) == []
    assert p.feed(data[7:]) == [pkt(1)]

def test_packet_split_byte_by_bytes():
    p = StreamParser()
    data = serialize(pkt(1))
    out = []
    for i in range(len(data)):
        out += p.feed(data[i : i + 1])
    assert out == [pkt(1)]

def test_two_packets_one_chunk():
    p = StreamParser()
    data = serialize(pkt(1)) + serialize(pkt(2))
    assert p.feed(data) == [pkt(1), pkt(2)]

def test_garbage_before_magic():
    p = StreamParser()
    bad = bytearray(serialize(pkt(99)))
    bad[-1] ^= 0xFF
    data = serialize(pkt(1)) + bytes(bad) + serialize(pkt(2))
    assert p.feed(data) == [pkt(1), pkt(2)]
    assert p.bad_packets == 1

def test_half_magic_at_chunk_end():
    p = StreamParser()
    data = serialize(pkt(1))
    assert p.feed(b"\x00\x00\xaa") == []
    assert p.feed(b"\x55" + data[2:]) == [pkt(1)]

def test_stats_start_at_zero():
    p = StreamParser()
    assert p.dropped_bytes == 0
    assert p.bad_packets == 0