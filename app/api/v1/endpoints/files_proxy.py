"""
Proxy endpoint for S3 files to handle CORS.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import httpx

router = APIRouter()

@router.get("/proxy/s3/{path:path}")
async def proxy_s3_file(path: str):
    """
    Proxy S3 files through backend to handle CORS.
    Usage: /api/v1/files/proxy/s3/uploads/file.stl
    """
    s3_url = f"https://s3.twcstorage.ru/66fcbd3b-259fc9df-4acc-4f84-bb9b-1ab070192e19/{path}"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(s3_url, timeout=30.0)
            response.raise_for_status()
            
            return StreamingResponse(
                iter([response.content]),
                media_type=response.headers.get("content-type", "application/octet-stream"),
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Cache-Control": "public, max-age=31536000"
                }
            )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=404, detail=f"File not found: {str(e)}")
