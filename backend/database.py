from sqlalchemy import create_engine, Column, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
import uuid
import os

from backend.config import DB_PATH

Base = declarative_base()

class MemoryEvent(Base):
    __tablename__ = 'memory_events'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow)
    source_type = Column(String(50))  # text, doc, image, audio, url
    source_path = Column(Text)
    content_hash = Column(String(64), unique=True)
    
    raw_text = Column(Text)
    vision_caption = Column(Text, nullable=True)
    metadata_json = Column(JSON, default={})
    
    summary_1line = Column(Text)
    summary_short = Column(Text) # Bullets
    
    entities = Column(JSON, default=[]) # Extracted list of entity names
    topics = Column(JSON, default=[])   # Extracted list of topic names
    intent_label = Column(String(100))
    
    embedding_ref = Column(String(50)) # ID/Index in FAISS
    
    action_items = relationship("ActionItem", back_populates="event", cascade="all, delete-orphan")
    graph_edges_from = relationship("GraphEdge", foreign_keys="[GraphEdge.from_event_id]", back_populates="from_event")
    graph_edges_to = relationship("GraphEdge", foreign_keys="[GraphEdge.to_event_id]", back_populates="to_event")

class ActionItem(Base):
    __tablename__ = 'action_items'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task = Column(Text, nullable=False)
    owner = Column(String(100))
    due_date = Column(DateTime, nullable=True)
    priority = Column(String(20)) # high, medium, low
    status = Column(String(20), default="open") # open, done
    evidence_event_id = Column(String(36), ForeignKey('memory_events.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    event = relationship("MemoryEvent", back_populates="action_items")

class Entity(Base):
    __tablename__ = 'entities'
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), unique=True)
    description = Column(Text)
    
class Topic(Base):
    __tablename__ = 'topics'
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), unique=True)

class GraphEdge(Base):
    __tablename__ = 'graph_edges'
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    from_event_id = Column(String(36), ForeignKey('memory_events.id'))
    to_event_id = Column(String(36), ForeignKey('memory_events.id'))
    relation_type = Column(String(50)) # temporal, causal, related
    
    from_event = relationship("MemoryEvent", foreign_keys=[from_event_id], back_populates="graph_edges_from")
    to_event = relationship("MemoryEvent", foreign_keys=[to_event_id], back_populates="graph_edges_to")


# Ensure directory exists for DB
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

engine = create_engine(f"sqlite:///{DB_PATH}")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
