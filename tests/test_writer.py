import queue
import time

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from telemetry.db import Base
from telemetry.models import Telemetry
from telemetry.protocol import TelemetryPacket
from telemetry.writer import DbWriter


def make_session_factory():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool,
                           )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)

def pkt(i):
    return TelemetryPacket(1_700_000_000 + i, 40.0, 12_000, i)

def test_flushes_on_batch_size():
    q = queue.Queue()
    sf = make_session_factory()
    w = DbWriter(q, sf, batch_size=5, batch_timeout=10.0)
    w.start()
    for i in range(5):
        q.put(pkt(i))
    deadline = time.monotonic() + 1
    while w.written < 5 and time.monotonic() < deadline:
        time.sleep(0.01)
    w.stop()
    with sf() as s:
        assert s.query(Telemetry).count() == 5

def test_flushes_on_timeout():
    q = queue.Queue()
    sf = make_session_factory()
    w = DbWriter(q, sf, batch_size=100, batch_timeout=0.1)
    w.start()
    q.put(pkt(1))
    time.sleep(0.3)
    w.stop()
    with sf() as s:
        assert s.query(Telemetry).count() == 1

def test_stop_flushes_remaining():
    q = queue.Queue()
    sf = make_session_factory()
    w = DbWriter(q, sf, batch_size=100, batch_timeout=10.0)
    w.start()
    for i in range(3):
        q.put(pkt(i))
    w.stop()
    with sf() as s:
        assert s.query(Telemetry).count() == 3
