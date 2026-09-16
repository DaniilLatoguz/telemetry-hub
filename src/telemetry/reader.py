import logging
import threading
import time
from collections.abc import Callable

import serial

from telemetry.protocol import TelemetryPacket
from telemetry.stream import StreamParser

log = logging.getLogger(__name__)

OnPacket = Callable[[TelemetryPacket], None]

class SerialReader:
    """Reads a serial port in a daemon thread, calls on_packet for each packet.

    Design:
    - on_packet is a callback, not a queue. Caller decides what to do with
    packets (put in queue, write to DB, forward to asyncio). This keeps
    the reader unaware of consumers.
    - serial_factory is injectable so tests can pass a fake port."""

    def __init__(
            self,
            port: str,
            baud: int,
            on_packet: OnPacket,
            serial_factory: Callable[..., serial.Serial] = serial.Serial,
            read_size: int = 256,
            reconnect_delay: float = 1.0
    ) -> None:
        self._port = port
        self._baud = baud
        self._on_packet = on_packet
        self._factory = serial_factory
        self._read_size = read_size
        self._reconnect_delay = reconnect_delay

        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="serial-reader, daemon=True)")
        self._parser = StreamParser()
        self.last_packet_at: float | None = None

    def start(self) -> None:
        self._thread.start()

    def stop(self, timeout: float = 2.0) -> None:
        """Signal the thread to stop and wait for it."""
        self._stop.set()
        self._thread.join(timeout=timeout)
        if self._thread.is_alive():
            log.warning("reader did not stop in time")

    @property
    def is_running(self) -> bool:
        return self._thread.is_alive()

    def _run(self) -> None:
        """Tread body. Reconnects on port errors, exits when stop is set."""
        while not self._stop.is_set():
            try:
                self._read_loop()
            except serial.SerialException as exc:
                log.warning("port error: %s; reconnecting in %.1fs", exc, self._reconnect_delay)
                self._stop.wait(self._reconnect_delay)

    def _read_loop(self) -> None:
        """Open port, read until stop is set. Let SerialException propagate."""
        port = self._factory(self._port, self._baud, timeout=0.1)
        try:
            while not self._stop.is_set():
                chunk = port.read(self._read_size)
                if not chunk:
                    continue
                for pkt in self._parser.feed(chunk):
                    self.last_packet_at = time.monotonic()
                    self._on_packet(pkt)
        finally:
            port.close()


