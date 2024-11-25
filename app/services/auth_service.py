from fastapi import Security, HTTPException
from fastapi.security.api_key import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN
from app.config import settings

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(api_key_header)):
  if api_key != settings.API_KEY:
      raise HTTPException(
          status_code=HTTP_403_FORBIDDEN,
          detail="Invalid API Key"
      )
  return api_key