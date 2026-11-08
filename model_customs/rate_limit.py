"""Cross-process token bucket shared by every NVIDIA model and request path."""
import asyncio
import sqlite3
import time
from .config import ROOT

class NvidiaLimiter:
    def __init__(self, path=None, rpm=30.0, capacity=1.0, clock=time.time, sleep=asyncio.sleep):
        if not 0 < rpm <= 30 or not 1 <= capacity <= 2:
            raise ValueError('Demo limiter must stay at <=30 rpm with capacity <=2')
        self.path=path or ROOT/'.cache/nvidia-rate.sqlite3'
        self.rate=rpm/60
        self.capacity=capacity
        self.clock=clock
        self.sleep=sleep

    def reserve(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with sqlite3.connect(self.path,timeout=10) as db:
            db.execute('CREATE TABLE IF NOT EXISTS bucket (id INTEGER PRIMARY KEY, tokens REAL, updated REAL)')
            db.execute('BEGIN IMMEDIATE')
            now=self.clock()
            row=db.execute('SELECT tokens,updated FROM bucket WHERE id=1').fetchone()
            tokens=self.capacity if row is None else min(self.capacity,row[0]+max(0,now-row[1])*self.rate)
            delay=0 if tokens>=1 else (1-tokens)/self.rate
            if delay==0: tokens-=1
            db.execute('INSERT OR REPLACE INTO bucket VALUES (1,?,?)',(tokens,max(now,row[1]) if row else now))
            return delay

    async def acquire(self):
        while True:
            delay=await asyncio.to_thread(self.reserve)
            if delay<=0:return
            await self.sleep(delay)

SHARED_LIMITER=NvidiaLimiter()

async def nvidia_request(client, method, url, **kwargs):
    """Rate-limit every attempt and back off 429; errors never include provider body."""
    for attempt in range(3):
        await SHARED_LIMITER.acquire()
        response=await client.request(method,url,**kwargs)
        if response.status_code!=429 or attempt==2:return response
        try: retry=float(response.headers.get('retry-after',0))
        except ValueError: retry=0
        await asyncio.sleep(min(max(2**attempt,retry),30))
