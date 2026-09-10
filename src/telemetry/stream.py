"""Reassemble packets from an arbitrary stream of byte chunks"""
from telemetry.protocol import HEADER_LEN, MAGIC, ProtocolError, TelemetryPacket, parse


class StreamParser:
    def __init__(self) -> None:
        self._buf = bytearray()
        self.dropped_bytes = 0
        self.bad_packets = 0

    def feed(self, chunk: bytes) -> list[TelemetryPacket]:
        """Append chunk to buffer, return all packets that are now complete.

                Algorithm:
                1. self._buf += chunk
                2. packets = []
                3. loop:
                   a. idx = self._buf.find(MAGIC)
                   b. if idx == -1:
                        # магии нет. Но последний байт может быть 0xAA (половина магии).
                        # Сохрани последний байт, если он == 0xAA, остальное выбрось
                        # (посчитай в dropped_bytes). break
                   c. if idx > 0:
                        # мусор перед магией — выбросить, посчитать. Продолжить.
                   d. if len(self._buf) < HEADER_LEN:
                        break   # не хватает даже заголовка — ждём следующий feed
                   e. length = self._buf[2]
                      total = HEADER_LEN + length + 1
                   f. if len(self._buf) < total:
                        break   # пакет неполный — ждём
                   g. try:
                        pkt = parse(bytes(self._buf[:total]))
                      except ProtocolError:
                        # битый пакет. Выбросить ТОЛЬКО первый байт (0xAA)
                        # и искать следующую магию с текущей позиции.
                        self.bad_packets += 1
                        del self._buf[:1]
                        continue
                   h. packets.append(pkt)
                      del self._buf[:total]
                4. return packets
                """
        self._buf += chunk
        packets = []
        while True:
            idx = self._buf.find(MAGIC)
            if idx == -1:
                if self._buf[-1:] == b"\xaa":
                    self.dropped_bytes += len(self._buf) - 1
                    del self._buf[:-1]
                else:
                    self.dropped_bytes += len(self._buf)
                    self._buf.clear()
                break

            if idx > 0:
                self.dropped_bytes += len(self._buf[:idx])
                del self._buf[:idx]

            if len(self._buf) < HEADER_LEN:
                break

            length = self._buf[2]
            total = HEADER_LEN + length + 1

            if len(self._buf) < total:
                break
            try:
                pkt = parse(bytes(self._buf[:total]))
            except ProtocolError:
                self.bad_packets += 1
                del self._buf[:1]
                continue
            packets.append(pkt)
            del self._buf[:total]
        return packets







