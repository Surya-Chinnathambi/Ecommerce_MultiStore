"""
Performance Metrics Dashboard
Collects and displays API performance metrics, database stats, and system health
"""
from typing import Dict, List
from datetime import datetime, timedelta
from collections import defaultdict
import time
import os
import asyncio


class PerformanceMetrics:
    """Collect and analyze performance metrics"""
    
    def __init__(self):
        self.request_times = defaultdict(list)
        self.error_counts = defaultdict(int)
        self.endpoint_calls = defaultdict(int)
        self.start_time = datetime.utcnow()
    
    def record_request(self, endpoint: str, duration_ms: float, status_code: int):
        """Record API request metrics"""
        self.request_times[endpoint].append(duration_ms)
        self.endpoint_calls[endpoint] += 1
        
        if status_code >= 400:
            self.error_counts[endpoint] += 1
    
    def get_endpoint_stats(self, endpoint: str) -> Dict:
        """Get statistics for a specific endpoint"""
        times = self.request_times.get(endpoint, [])
        
        if not times:
            return {
                "endpoint": endpoint,
                "calls": 0,
                "avg_response_time": 0,
                "min_response_time": 0,
                "max_response_time": 0,
                "errors": 0,
            }
        
        return {
            "endpoint": endpoint,
            "calls": self.endpoint_calls[endpoint],
            "avg_response_time": round(sum(times) / len(times), 2),
            "min_response_time": round(min(times), 2),
            "max_response_time": round(max(times), 2),
            "p95_response_time": round(sorted(times)[int(len(times) * 0.95)], 2) if len(times) > 1 else round(times[0], 2),
            "errors": self.error_counts.get(endpoint, 0),
            "error_rate": round(self.error_counts.get(endpoint, 0) / self.endpoint_calls[endpoint] * 100, 2),
        }
    
    def get_all_stats(self) -> List[Dict]:
        """Get statistics for all endpoints"""
        return [
            self.get_endpoint_stats(endpoint)
            for endpoint in self.endpoint_calls.keys()
        ]
    
    def get_system_metrics(self) -> Dict:
        """Get system-level metrics"""
        import resource
        try:
            # Get process resource usage
            usage = resource.getrusage(resource.RUSAGE_SELF)
            return {
                "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
                "cpu_time_seconds": usage.ru_utime + usage.ru_stime,
                "max_rss_mb": round(usage.ru_maxrss / 1024, 2) if hasattr(usage, 'ru_maxrss') else 0,
            }
        except:
            # Fallback if resource module not available
            return {
                "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
            }
    
    def get_summary(self) -> Dict:
        """Get summary of all metrics"""
        all_times = []
        for times in self.request_times.values():
            all_times.extend(times)
        
        total_calls = sum(self.endpoint_calls.values())
        total_errors = sum(self.error_counts.values())
        
        return {
            "total_requests": total_calls,
            "total_errors": total_errors,
            "error_rate": round(total_errors / total_calls * 100, 2) if total_calls > 0 else 0,
            "avg_response_time": round(sum(all_times) / len(all_times), 2) if all_times else 0,
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
            "endpoints_tracked": len(self.endpoint_calls),
        }


# Global metrics instance
metrics = PerformanceMetrics()


# Middleware for automatic metrics collection
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect request metrics"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        duration_ms = (time.time() - start_time) * 1000
        endpoint = request.url.path
        
        # Record metrics
        metrics.record_request(endpoint, duration_ms, response.status_code)
        
        # Add metrics headers
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
        
        return response


# FastAPI endpoints for metrics dashboard
from fastapi import APIRouter
from app.schemas.schemas import APIResponse

router = APIRouter()


@router.get("/metrics/summary", response_model=APIResponse)
async def metrics_summary():
    """Get overall metrics summary"""
    summary = metrics.get_summary()
    return APIResponse(success=True, data=summary)


@router.get("/metrics/endpoints", response_model=APIResponse)
async def endpoint_metrics():
    """Get metrics for all endpoints"""
    stats = metrics.get_all_stats()
    # Sort by call count
    stats.sort(key=lambda x: x['calls'], reverse=True)
    return APIResponse(success=True, data=stats)


@router.get("/metrics/system", response_model=APIResponse)
async def system_metrics():
    """Get system-level metrics"""
    system = metrics.get_system_metrics()
    return APIResponse(success=True, data=system)


@router.get("/metrics/slowest", response_model=APIResponse)
async def slowest_endpoints(limit: int = 10):
    """Get slowest endpoints"""
    stats = metrics.get_all_stats()
    stats.sort(key=lambda x: x['avg_response_time'], reverse=True)
    return APIResponse(success=True, data=stats[:limit])


@router.get("/metrics/errors", response_model=APIResponse)
async def error_metrics():
    """Get error metrics"""
    stats = metrics.get_all_stats()
    # Filter endpoints with errors
    error_stats = [s for s in stats if s['errors'] > 0]
    error_stats.sort(key=lambda x: x['error_rate'], reverse=True)
    return APIResponse(success=True, data=error_stats)


@router.post("/metrics/reset")
async def reset_metrics():
    """Reset all metrics (admin only)"""
    global metrics
    metrics = PerformanceMetrics()
    return APIResponse(success=True, data={"message": "Metrics reset successfully"})
