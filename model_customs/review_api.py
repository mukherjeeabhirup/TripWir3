"""Optional read-only review routes; existing accepted replay gates stay unchanged."""
import asyncio
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from . import review_data as data

router = APIRouter(prefix='/api/review')

@router.get('/catalog')
async def catalog(): return data.catalog()

@router.get('/comparison')
async def comparison(): return data.comparison()

@router.get('/{run_id}/bundle')
async def bundle(run_id: str):
    try: return data.bundle(run_id)
    except (ValueError, OSError): raise HTTPException(404, 'Historical evidence unavailable') from None

@router.get('/{run_id}/files/{name}')
async def file(run_id: str, name: str):
    try: path = data.source_path(run_id, name)
    except ValueError: raise HTTPException(404, 'Evidence file unavailable') from None
    return FileResponse(path, media_type='text/plain', headers={'X-Content-Type-Options': 'nosniff'})

@router.get('/{run_id}/events')
async def events(run_id: str):
    try: trace = data.events(run_id)
    except (ValueError, OSError): raise HTTPException(404, 'Historical evidence unavailable') from None
    async def stream():
        for event in trace:
            yield 'data: ' + json.dumps(event) + '\n\n'
            await asyncio.sleep(.12)
    return StreamingResponse(stream(), media_type='text/event-stream', headers={'Cache-Control': 'no-cache'})
