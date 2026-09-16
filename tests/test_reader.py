import time

import serial

from telemetry.protocol import TelemetryPacket, serialize
from telemetry.reader import SerialReader


class FakeSerial:
    """Returns pre-defined chunks one per read(), then empty bytes forever."""

    def __init__(self, chunks: list[bytes], fail_after: int | None = None):
        self._chunks = list(chunks)
        self._fail_after = fail_after
        self._reads = 0
        self.closed = False

    def read(self, n:int) -> bytes:
        self._reads += 1
        if self._fail_after is not None and self._reads > self._fail_after:
            raise serial.SerialException("simulated port loss")
        if self._chunks:
            return self._chunks.pop(0)
        time.sleep(0.01)
        return b""

    def close(self) -> None:
        self.closed = True

def pkt (frame_id: int) -> TelemetryPacket:
    return TelemetryPacket(1_700_000_000, 40.0, 12_000, frame_id)

def wait_until(cond, timeout=1.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if cond():
            return True
        time.sleep(0.005)
    return False

def make_reader(chunks, **kw):
    received = []
    fake = FakeSerial(chunks, **kw)
    reader = SerialReader(
        port="fake", baud=115200,
        on_packet=received.append,
        serial_factory=lambda *a, **k: fake,
        reconnect_delay=0.05,
    )
    return reader, received, fake

def test_packets_arrive_via_callback():
    data = serialize(pkt(1)) + serialize(pkt(2))
    reader, received, _ = make_reader([data[:5], data[5:20], data[20:]])
    reader.start()
    assert wait_until(lambda: len(received) == 2)
    reader.stop()
    assert received == [pkt(1), pkt(2)]

def test_stop_terminates_thread():
    reader, _, fake = make_reader([])
    reader.start()
    assert reader.is_running
    reader.stop(timeout=1.0)
    assert not reader.is_running
    assert fake.closed

def test_bad_packet_does_not_kill_thread():
    bad = bytearray(serialize(pkt(99)))
    bad[-1] ^= 0xFF
    reader, received, _ = make_reader([serialize(pkt(1)), bytes(bad), serialize(pkt(2))])
    reader.start()
    assert wait_until(lambda: len(received) == 2)
    reader.stop()
    assert [p.frame_id for p in received] == [1, 2]

def test_reconnects_after_port_error():
    """Port dies after 2 reads; reader must reopen and keep going."""
    calls = {"n": 0}
    data = serialize(pkt(1))

    def factory(*a, **k):
        calls["n"] += 1
        return FakeSerial([data], fail_after=2) if calls["n"] == 1 else FakeSerial([data])

    received = []
    reader = SerialReader("fake",
                          115200,
                          received.append,
                          serial_factory=factory,
                          reconnect_delay=0.05)
    reader.start()
    assert wait_until(lambda: calls["n"] >= 2, timeout=2.0)
    assert wait_until(lambda: len(received) >= 2, timeout=2.0)
    reader.stop()

def test_last_packet_at_updated():
    reader, received, _ = make_reader([serialize(pkt(1))])
    assert reader.last_packet_at is None
    reader.start()
    assert wait_until(lambda: len(received) == 1)
    reader.stop()
    assert reader.last_packet_at is not None


