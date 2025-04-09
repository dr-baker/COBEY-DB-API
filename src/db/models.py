from pydantic import BaseModel
from typing import Dict, Optional
from datetime import datetime

class User(BaseModel):
    user_id: str
    firebase_data: Dict
    body_data: Dict

class Session(BaseModel):
    session_id: str
    user_id: str
    ts_start: datetime
    exercises_data: Dict
    device_type: str
    device_os: str
    region: str
    ip: str
    app_version: str

class EventLog(BaseModel):
    ts: datetime
    user_id: str
    session_id: str
    event_type: str
    event_data: Dict
    event_source: str
    log_level: str
    app_version: str 