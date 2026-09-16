import logging
import queue
import sys

from telemetry.reader import SerialReader

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(threadName)s %(message)s")

q: queue.Queue = queue.Queue()
reader = SerialReader(sys.argv[1], 115200, on_packet=q.put)
reader.start()
try:
    while True:
        pkt = q.get()
        print(f"frame={pkt.frame_id} t={pkt.temperature:.1f} v={pkt.voltage_mv}")
except KeyboardInterrupt:
    reader.stop()