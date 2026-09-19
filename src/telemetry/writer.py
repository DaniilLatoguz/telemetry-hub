"""Consumes packets from a queue and writes them to DB in batches."""

import logging
import queue
import threading
import time

from telemetry.models import Telemetry
from telemetry.protocol import TelemetryPacket

log = logging.getLogger(__name__)

class DbWriter:
    """Batches packets: flush when batch_size reached OR batch_timeout elapsed.

    Why batches: one INSERT per packet = one transaction per packet.
    At 100 packets/s that is 100 round-trips. Batching 50 = 2 round-trips.
    """

    def __init__(
            self,
            in_queue: queue.Queue,
            session_factory,
            batch_size: int = 50,
            batch_timeout: float = 1.0,
    ) -> None:
        self._queue = in_queue
        self._session_factory = session_factory
        self._batch_size = batch_size
        self._batch_timeout = batch_timeout
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="db-writer", daemon=True)
        self.written = 0

    def start(self) -> None:
        self._thread.start()

    def stop(self, timeout: float = 5.0) -> None:
        """Set stop, join. The thread must flush remaining batch before exit."""
        self._stop.set()
        self._thread.join(timeout)

    def _run(self) -> None:
        batch = []
        last_flush = time.monotonic()
        while not self._stop.is_set() or not self._queue.empty():
            try:
                pkt = self._queue.get(timeout=0.1)
                batch.append(pkt)
            except queue.Empty:
                pass
            due = (len(batch) >= self._batch_size
                   or (batch and time.monotonic() - last_flush >= self._batch_timeout))
            if due:
                self._flush(batch)
                batch = []
                last_flush = time.monotonic()
        if batch:
            self._flush(batch)

    def _flush(self, batch: list[TelemetryPacket]) -> None:
        """Insert batch in ONE transaction."""

        rows = [Telemetry(timestamp=p.timestamp, temperature=p.temperature,
                          voltage_mv=p.voltage_mv, frame_id=p.frame_id) for p in batch]
        with self._session_factory() as session:
            session.add_all(rows)
            session.commit()
        self.written += len(rows)
        log.debug("flushed %d rows", len(rows))
