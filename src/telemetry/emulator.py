"""Fake device: writes telemetry packets to a serial port at a fixed rate.

Usage:
    python -m telemetry.emulator --port /dev/pts/2 --interval 0.1
"""

import argparse
import random
import signal
import time

import serial

from telemetry.protocol import TelemetryPacket, serialize


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--port", required=True, help="serial prot, e.g. /dev/pts/2")
    p.add_argument("--baud", type=int, default=115200)
    p.add_argument("--interval", type=float, default=0.1, help="seconds between packets")
    p.add_argument("--corrupt", type=float, default=0.0, help="probability of corrupt CRC")
    return p

def next_packet(frame_id: int) -> TelemetryPacket:
    """Generate plausible telemetry.

    TODO:
    - temperature: random.gauss(40.0, 1.5)
    - voltage: int(random.gauss(12000, 50))
    - timestamp: int(time.time())
    """
    temperature = random.gauss(40.0, 1.5)
    voltage = int(random.gauss(12000, 50))
    timestamp = int(time.time())
    return TelemetryPacket(timestamp, temperature, voltage, frame_id)

def maybe_corrupt(data: bytes, probability: float) -> bytes:
    """With given probability flip the last byte (the CRC).

    TODO: random.random() < probability -> flip data[-1] via bytearray
    """
    if random.random() < probability:
        data = bytearray(data)
        data[-1] ^= 0xFF
        return bytes(data)
    return data

def main() -> None:
    args = build_parser().parse_args()
    running = True

    def stop(*_):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, stop)

    with serial.Serial(args.port, args.baud) as port:
        frame_id = 0
        while running:
            pkt = next_packet(frame_id)
            port.write(maybe_corrupt(serialize(pkt), args.corrupt))
            frame_id += 1
            time.sleep(args.interval)

        print(f"stopped after {frame_id} packets")

if __name__ == "__main__":
    main()

