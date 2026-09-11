from telemetry.emulator import build_parser, maybe_corrupt, next_packet
from telemetry.protocol import serialize


def test_next_packet_is_plausible():
    pkt = next_packet(frame_id=5)
    assert pkt.frame_id == 5
    assert 30.0 < pkt.temperature < 50.0
    assert 11_000 < pkt.voltage_mv < 13_000

def test_no_corruption_at_zero_probability():
    data = serialize(next_packet(1))
    assert maybe_corrupt(data, 0.0) == data

def test_always_corrupt_at_one():
    data = serialize(next_packet(1))
    corrupted = maybe_corrupt(data, 1.0)
    assert corrupted != data
    assert len(corrupted) == len(data)

def test_parser_defaults():
    args = build_parser().parse_args(["--port", "/dev/null"])
    assert args.baud == 115200
    assert args.interval == 0.1

    