import json
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, field_validator


class JobResponse(BaseModel):
    id:                int
    filename:          str
    status:            str
    created_at:        datetime
    completed_at:      Optional[datetime]
    total_frames:      Optional[int]
    anomaly_frames:    Optional[int]
    suspicious_frames: Optional[int]
    normal_frames:     Optional[int]
    fps:               Optional[float]

    model_config = {"from_attributes": True}


class EventResponse(BaseModel):
    id:                int
    job_id:            int
    frame_number:      int
    timestamp_sec:     float
    classification:    str
    anomaly_score:     float
    triggered_signals: Optional[List[str]]
    created_at:        datetime

    model_config = {"from_attributes": True}

    @field_validator("triggered_signals", mode="before")
    @classmethod
    def parse_signals(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v or []


class AnomalyTimestamp(BaseModel):
    start: float
    end:   float


class AnalysisSummary(BaseModel):
    job_id:             int
    duration_sec:       float
    normal_count:       int
    suspicious_count:   int
    anomaly_count:      int
    anomaly_percentage: float
    anomaly_timestamps: List[AnomalyTimestamp]
