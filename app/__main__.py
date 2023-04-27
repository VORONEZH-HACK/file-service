from app.db import init_db, get_session, engine
from app.models import File

from typing import Dict, Optional, List
from fastapi import FastAPI, UploadFile, HTTPException, Header, Depends, Query
from botocore.exceptions import NoCredentialsError
from datetime import date, datetime
from pydantic import BaseModel, constr, Field
from sqlmodel import Session, select
from uuid import UUID

import uvicorn
import asyncio
import boto3
import json
import logging
import httpx
import os


app = FastAPI()

s3 = boto3.client(
    service_name='s3',
    endpoint_url='https://storage.yandexcloud.net'
)

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

log = logging.getLogger(__name__)


@app.on_event("startup")
async def startup_event():
    log.info('Initializing API ...')
    init_db()


@app.on_event("shutdown")
async def shutdown_event():
    log.info('Shutting down API')


async def validate_token(access_token: str) -> UUID:
    async with httpx.AsyncClient() as client:
        response = await client.get('auth:8080/check', headers={"access-token": access_token})
        
        if response.status_code != 200:
            return None

        user_data = response.json()
        return UUID(user_data["user"])


@app.post("/file", response_model=File)
async def upload_file(file: UploadFile, filetype: str = Query(None), access_token: str = Header(None), db: Session = Depends(get_session)):
    user_id = await validate_token(access_token)
    if not user_id: 
        raise HTTPException(status_code=400, detail="Invalid access token")

    try:
        s3.upload_fileobj(file.file, 'files-heap', file.filename)
    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="Missing AWS credentials")

    new_file = File(name=file.filename, user_id=user_id, type=filetype)
    db.add(new_file)
    db.commit()
    db.refresh(new_file)

    return new_file


@app.get("/file", response_model=List[File])
async def get_files(user: str, access_token: str = Header(None), db: Session = Depends(get_session)):
    user_id = await validate_token(access_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid access token")

    try:
        user_uuids = [UUID(id) for id in user.split(",")]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    files = db.exec(select(File).where(File.user_id.in_(user_uuids))).all()

    if not files:
        return []

    return files


@app.get("/file/{file_id}", response_model=str)
async def get_file(file_id: UUID, access_token: str = Header(None), db: Session = Depends(get_session)):
    user_id = await validate_token(access_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid access token")

    file = db.exec(select(File).where(File.id == file_id)).first()

    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    try:
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': 'files-heap', 'Key': file.name},
            ExpiresIn=600
        )
    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="Missing AWS credentials")

    return url


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
