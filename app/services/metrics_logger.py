"""
Metrics Logger - Tracks and logs system performance metrics
"""
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import threading
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class MetricsLogger:
    """Singleton class for logging system metrics"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize metrics logger"""
        if self._initialized:
            return
        
        self._initialized = True
        self.metrics_file = Path("logs/metrics.jsonl")
        self.metrics_file.parent.mkdir(exist_ok=True)
        
        # In-memory metrics storage (last 1000 entries per metric type)
        self.metrics = {
            "stt": deque(maxlen=1000),
            "tts": deque(maxlen=1000),
            "chat": deque(maxlen=1000),
            "retrieval": deque(maxlen=1000),
            "document": deque(maxlen=1000),
            "feedback": deque(maxlen=1000)
        }
        
        # Aggregated metrics
        self.aggregated = defaultdict(lambda: {
            "count": 0,
            "total_time": 0,
            "avg_time": 0,
            "min_time": float('inf'),
            "max_time": 0
        })
    
    def _write_metric(self, metric_type: str, data: Dict[str, Any]):
        """Write metric to file"""
        try:
            metric_entry = {
                "timestamp": datetime.now().isoformat(),
                "type": metric_type,
                "data": data
            }
            
            with open(self.metrics_file, "a") as f:
                f.write(json.dumps(metric_entry) + "\n")
        except Exception as e:
            logger.error(f"Error writing metric: {str(e)}")
    
    def log_stt_metrics(self, duration_ms: float, file_size_mb: float, text_length: int):
        """Log speech-to-text metrics"""
        metric = {
            "duration_ms": duration_ms,
            "file_size_mb": file_size_mb,
            "text_length": text_length,
            "chars_per_second": (text_length / duration_ms * 1000) if duration_ms > 0 else 0
        }
        
        self.metrics["stt"].append(metric)
        self._write_metric("stt", metric)
        self._update_aggregated("stt", duration_ms)
    
    def log_tts_metrics(self, duration_ms: float, text_length: int, audio_size_kb: float):
        """Log text-to-speech metrics"""
        metric = {
            "duration_ms": duration_ms,
            "text_length": text_length,
            "audio_size_kb": audio_size_kb,
            "chars_per_second": (text_length / duration_ms * 1000) if duration_ms > 0 else 0
        }
        
        self.metrics["tts"].append(metric)
        self._write_metric("tts", metric)
        self._update_aggregated("tts", duration_ms)
    
    def log_chat_metrics(
        self,
        session_id: str,
        agent: str,
        response_time_ms: float,
        tokens_used: int
    ):
        """Log chat interaction metrics"""
        metric = {
            "session_id": session_id,
            "agent": agent,
            "response_time_ms": response_time_ms,
            "tokens_used": tokens_used
        }
        
        self.metrics["chat"].append(metric)
        self._write_metric("chat", metric)
        self._update_aggregated(f"chat_{agent}", response_time_ms)
    
    def log_retrieval_metrics(
        self,
        agent: str,
        query_length: int,
        results_count: int,
        retrieval_time_ms: float
    ):
        """Log document retrieval metrics"""
        metric = {
            "agent": agent,
            "query_length": query_length,
            "results_count": results_count,
            "retrieval_time_ms": retrieval_time_ms
        }
        
        self.metrics["retrieval"].append(metric)
        self._write_metric("retrieval", metric)
        self._update_aggregated(f"retrieval_{agent}", retrieval_time_ms)
    
    def log_document_processing(
        self,
        agent: str,
        filename: str,
        chunks: int,
        processing_time_ms: float,
        file_size_mb: float
    ):
        """Log document processing metrics"""
        metric = {
            "agent": agent,
            "filename": filename,
            "chunks": chunks,
            "processing_time_ms": processing_time_ms,
            "file_size_mb": file_size_mb,
            "chunks_per_mb": chunks / file_size_mb if file_size_mb > 0 else 0
        }
        
        self.metrics["document"].append(metric)
        self._write_metric("document", metric)
        self._update_aggregated("document_processing", processing_time_ms)
    
    def log_feedback(
        self,
        session_id: str,
        message_id: str,
        rating: int,
        comment: Optional[str] = None
    ):
        """Log user feedback"""
        metric = {
            "session_id": session_id,
            "message_id": message_id,
            "rating": rating,
            "comment": comment
        }
        
        self.metrics["feedback"].append(metric)
        self._write_metric("feedback", metric)
    
    def _update_aggregated(self, key: str, time_ms: float):
        """Update aggregated metrics"""
        agg = self.aggregated[key]
        agg["count"] += 1
        agg["total_time"] += time_ms
        agg["avg_time"] = agg["total_time"] / agg["count"]
        agg["min_time"] = min(agg["min_time"], time_ms)
        agg["max_time"] = max(agg["max_time"], time_ms)
    
    def get_audio_metrics(self) -> Dict[str, Any]:
        """Get audio processing metrics summary"""
        stt_metrics = list(self.metrics["stt"])[-100:]  # Last 100
        tts_metrics = list(self.metrics["tts"])[-100:]
        
        return {
            "stt": {
                "total_processed": len(stt_metrics),
                "avg_duration_ms": sum(m["duration_ms"] for m in stt_metrics) / len(stt_metrics) if stt_metrics else 0,
                "avg_file_size_mb": sum(m["file_size_mb"] for m in stt_metrics) / len(stt_metrics) if stt_metrics else 0,
                "recent": stt_metrics[-5:] if stt_metrics else []
            },
            "tts": {
                "total_processed": len(tts_metrics),
                "avg_duration_ms": sum(m["duration_ms"] for m in tts_metrics) / len(tts_metrics) if tts_metrics else 0,
                "avg_audio_size_kb": sum(m["audio_size_kb"] for m in tts_metrics) / len(tts_metrics) if tts_metrics else 0,
                "recent": tts_metrics[-5:] if tts_metrics else []
            }
        }
    
    def get_chat_metrics(self) -> Dict[str, Any]:
        """Get chat metrics summary"""
        chat_metrics = list(self.metrics["chat"])[-100:]
        
        # Group by agent
        agent_metrics = defaultdict(list)
        for metric in chat_metrics:
            agent_metrics[metric["agent"]].append(metric)
        
        summary = {
            "total_interactions": len(chat_metrics),
            "by_agent": {}
        }
        
        for agent, metrics in agent_metrics.items():
            summary["by_agent"][agent] = {
                "count": len(metrics),
                "avg_response_time_ms": sum(m["response_time_ms"] for m in metrics) / len(metrics),
                "total_tokens": sum(m["tokens_used"] for m in metrics)
            }
        
        summary["recent"] = chat_metrics[-10:] if chat_metrics else []
        
        return summary
    
    def get_rag_metrics(self) -> Dict[str, Any]:
        """Get RAG metrics summary"""
        retrieval_metrics = list(self.metrics["retrieval"])[-100:]
        document_metrics = list(self.metrics["document"])[-50:]
        
        return {
            "retrieval": {
                "total_queries": len(retrieval_metrics),
                "avg_retrieval_time_ms": sum(m["retrieval_time_ms"] for m in retrieval_metrics) / len(retrieval_metrics) if retrieval_metrics else 0,
                "avg_results_count": sum(m["results_count"] for m in retrieval_metrics) / len(retrieval_metrics) if retrieval_metrics else 0,
                "recent": retrieval_metrics[-5:] if retrieval_metrics else []
            },
            "document_processing": {
                "total_documents": len(document_metrics),
                "total_chunks": sum(m["chunks"] for m in document_metrics),
                "avg_processing_time_ms": sum(m["processing_time_ms"] for m in document_metrics) / len(document_metrics) if document_metrics else 0,
                "recent": document_metrics[-5:] if document_metrics else []
            }
        }
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get overall system metrics"""
        return {
            "timestamp": datetime.now().isoformat(),
            "aggregated": dict(self.aggregated),
            "audio": self.get_audio_metrics(),
            "chat": self.get_chat_metrics(),
            "rag": self.get_rag_metrics(),
            "feedback_summary": self._get_feedback_summary()
        }
    
    def _get_feedback_summary(self) -> Dict[str, Any]:
        """Get feedback summary"""
        feedback = list(self.metrics["feedback"])
        
        if not feedback:
            return {"count": 0, "average_rating": 0}
        
        ratings = [f["rating"] for f in feedback]
        return {
            "count": len(feedback),
            "average_rating": sum(ratings) / len(ratings),
            "distribution": {
                "1": ratings.count(1),
                "2": ratings.count(2),
                "3": ratings.count(3),
                "4": ratings.count(4),
                "5": ratings.count(5)
            }
        }
