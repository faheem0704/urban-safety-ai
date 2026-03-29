from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from database.database import Base


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id              = Column(Integer, primary_key=True, index=True)
    filename        = Column(String,  nullable=False)
    status          = Column(String,  default="pending")   # pending/processing/complete/failed
    created_at      = Column(DateTime, default=datetime.utcnow)
    completed_at    = Column(DateTime, nullable=True)
    total_frames    = Column(Integer,  nullable=True)
    anomaly_frames  = Column(Integer,  nullable=True)
    suspicious_frames = Column(Integer, nullable=True)
    normal_frames   = Column(Integer,  nullable=True)
    fps             = Column(Float,   nullable=True)        # needed for duration_sec in summary

    events = relationship("AnomalyEvent", back_populates="job", cascade="all, delete-orphan")


class AnomalyEvent(Base):
    __tablename__ = "anomaly_events"

    id                = Column(Integer, primary_key=True, index=True)
    job_id            = Column(Integer, ForeignKey("analysis_jobs.id"), nullable=False, index=True)
    frame_number      = Column(Integer, nullable=False)
    timestamp_sec     = Column(Float,   nullable=False)
    classification    = Column(String,  nullable=False)      # NORMAL / SUSPICIOUS / ANOMALY
    anomaly_score     = Column(Float,   nullable=False)
    triggered_signals = Column(Text,    nullable=True)       # JSON-encoded list[str]
    created_at        = Column(DateTime, default=datetime.utcnow)

    job = relationship("AnalysisJob", back_populates="events")
