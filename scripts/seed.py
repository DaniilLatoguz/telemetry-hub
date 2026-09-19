"""Insert N fake rows fast, for index benchmarking."""

import random
import sys
import time

from sqlalchemy import insert

from telemetry.db import SessionLocal
from telemetry.models import Telemetry

N = int(sys.argv[1]) if len (sys.argv) > 1 else 1_000_000
BATCH = 10_000
base_ts = 1_700_000_000

t0 = time.perf_counter()
with SessionLocal() as s:
    for start in range(0, N, BATCH):
        rows = [
            {
                "timestamp": base_ts + i,
                "temperature": random.gauss(40, 1.5),
                "voltage_mv": int(random.gauss(12000, 50)),
                "frame_id": i,
            }
            for i in range(start, min(start + BATCH, N))
        ]
        s.execute(insert(Telemetry), rows)
        s.commit()
print(f"inserted {N} rows in {time.perf_counter() - t0:.1f}s")

