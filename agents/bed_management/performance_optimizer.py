"""
Performance Optimization with Caching and Query Optimization
"""
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
import time
import hashlib
import json
import threading
from functools import wraps
from collections import OrderedDict

class LRUCache:
    """Least Recently Used Cache implementation"""
    
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.cache = OrderedDict()
        self.access_times = {}
        self.hit_count = 0
        self.miss_count = 0
        self.lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        with self.lock:
            if key in self.cache:
                # Move to end (most recently used)
                value = self.cache.pop(key)
                self.cache[key] = value
                self.access_times[key] = datetime.now()
                self.hit_count += 1
                return value
            else:
                self.miss_count += 1
                return None
    
    def put(self, key: str, value: Any, ttl_minutes: Optional[int] = None):
        """Put item in cache"""
        with self.lock:
            # Remove oldest items if cache is full
            while len(self.cache) >= self.max_size:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                del self.access_times[oldest_key]
            
            self.cache[key] = {
                'data': value,
                'created_at': datetime.now(),
                'expires_at': datetime.now() + timedelta(minutes=ttl_minutes) if ttl_minutes else None
            }
            self.access_times[key] = datetime.now()
    
    def is_expired(self, key: str) -> bool:
        """Check if cache item is expired"""
        if key not in self.cache:
            return True
        
        item = self.cache[key]
        if item['expires_at'] and datetime.now() > item['expires_at']:
            with self.lock:
                del self.cache[key]
                del self.access_times[key]
            return True
        
        return False
    
    def clear_expired(self):
        """Clear all expired items"""
        with self.lock:
            expired_keys = []
            for key in self.cache:
                if self.is_expired(key):
                    expired_keys.append(key)
            
            for key in expired_keys:
                if key in self.cache:
                    del self.cache[key]
                if key in self.access_times:
                    del self.access_times[key]
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'hit_rate': round(hit_rate, 2),
            'total_requests': total_requests
        }

class QueryOptimizer:
    """Query optimization and performance monitoring"""
    
    def __init__(self):
        self.query_cache = LRUCache(max_size=200)
        self.query_stats = {}
        self.slow_query_threshold = 1.0  # seconds
        self.slow_queries = []
        
        # Cache TTL for different query types (in minutes)
        self.cache_ttl = {
            'bed_occupancy': 2,      # Bed occupancy changes frequently
            'patient_info': 5,       # Patient info changes less frequently
            'bed_availability': 1,   # Bed availability changes very frequently
            'patient_lookup': 10,    # Individual patient data is more stable
            'occupancy_status': 3,   # Overall status changes moderately
            'doctor_list': 60        # Doctor list rarely changes
        }
    
    def cache_key(self, query_type: str, params: Dict) -> str:
        """Generate cache key from query type and parameters"""
        # Sort parameters for consistent key generation
        sorted_params = json.dumps(params, sort_keys=True)
        key_string = f"{query_type}:{sorted_params}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def cached_query(self, query_type: str):
        """Decorator for caching query results"""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = self.cache_key(query_type, kwargs)
                
                # Try to get from cache
                cached_result = self.query_cache.get(cache_key)
                if cached_result and not self.query_cache.is_expired(cache_key):
                    return cached_result['data']
                
                # Execute query and measure time
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    
                    # Cache the result
                    ttl = self.cache_ttl.get(query_type, 5)
                    self.query_cache.put(cache_key, result, ttl)
                    
                    # Record query statistics
                    self._record_query_stats(query_type, execution_time, True)
                    
                    # Check for slow queries
                    if execution_time > self.slow_query_threshold:
                        self._record_slow_query(query_type, execution_time, kwargs)
                    
                    return result
                    
                except Exception as e:
                    execution_time = time.time() - start_time
                    self._record_query_stats(query_type, execution_time, False)
                    raise e
            
            return wrapper
        return decorator
    
    def _record_query_stats(self, query_type: str, execution_time: float, success: bool):
        """Record query execution statistics"""
        if query_type not in self.query_stats:
            self.query_stats[query_type] = {
                'total_queries': 0,
                'successful_queries': 0,
                'failed_queries': 0,
                'total_time': 0.0,
                'avg_time': 0.0,
                'min_time': float('inf'),
                'max_time': 0.0,
                'last_executed': None
            }
        
        stats = self.query_stats[query_type]
        stats['total_queries'] += 1
        stats['total_time'] += execution_time
        stats['avg_time'] = stats['total_time'] / stats['total_queries']
        stats['min_time'] = min(stats['min_time'], execution_time)
        stats['max_time'] = max(stats['max_time'], execution_time)
        stats['last_executed'] = datetime.now().isoformat()
        
        if success:
            stats['successful_queries'] += 1
        else:
            stats['failed_queries'] += 1
    
    def _record_slow_query(self, query_type: str, execution_time: float, params: Dict):
        """Record slow query for analysis"""
        slow_query = {
            'query_type': query_type,
            'execution_time': execution_time,
            'parameters': params,
            'timestamp': datetime.now().isoformat()
        }
        
        self.slow_queries.append(slow_query)
        
        # Keep only last 50 slow queries
        if len(self.slow_queries) > 50:
            self.slow_queries = self.slow_queries[-50:]
    
    def get_performance_stats(self) -> Dict:
        """Get comprehensive performance statistics"""
        cache_stats = self.query_cache.get_stats()
        
        # Calculate overall performance metrics
        total_queries = sum(stats['total_queries'] for stats in self.query_stats.values())
        total_time = sum(stats['total_time'] for stats in self.query_stats.values())
        avg_response_time = total_time / total_queries if total_queries > 0 else 0
        
        # Find slowest query types
        slowest_queries = sorted(
            [(qtype, stats['avg_time']) for qtype, stats in self.query_stats.items()],
            key=lambda x: x[1], reverse=True
        )[:5]
        
        return {
            'cache_performance': cache_stats,
            'query_statistics': self.query_stats,
            'overall_metrics': {
                'total_queries': total_queries,
                'average_response_time': round(avg_response_time, 3),
                'slow_queries_count': len(self.slow_queries),
                'cache_hit_rate': cache_stats['hit_rate']
            },
            'slowest_query_types': slowest_queries,
            'recent_slow_queries': self.slow_queries[-10:] if self.slow_queries else []
        }
    
    def optimize_query_cache(self):
        """Optimize cache by clearing expired items and adjusting TTL"""
        self.query_cache.clear_expired()
        
        # Adjust TTL based on query frequency and performance
        for query_type, stats in self.query_stats.items():
            if stats['avg_time'] > self.slow_query_threshold:
                # Increase cache time for slow queries
                current_ttl = self.cache_ttl.get(query_type, 5)
                self.cache_ttl[query_type] = min(current_ttl * 1.5, 30)  # Max 30 minutes
            elif stats['avg_time'] < 0.1:
                # Decrease cache time for fast queries
                current_ttl = self.cache_ttl.get(query_type, 5)
                self.cache_ttl[query_type] = max(current_ttl * 0.8, 1)  # Min 1 minute
    
    def get_cache_recommendations(self) -> List[str]:
        """Get recommendations for cache optimization"""
        recommendations = []
        cache_stats = self.query_cache.get_stats()
        
        if cache_stats['hit_rate'] < 50:
            recommendations.append("Cache hit rate is low. Consider increasing cache size or TTL values.")
        
        if cache_stats['size'] >= cache_stats['max_size'] * 0.9:
            recommendations.append("Cache is nearly full. Consider increasing max cache size.")
        
        # Check for frequently queried but slow operations
        for query_type, stats in self.query_stats.items():
            if stats['total_queries'] > 10 and stats['avg_time'] > self.slow_query_threshold:
                recommendations.append(f"Query type '{query_type}' is slow but frequently used. Consider database optimization.")
        
        if len(self.slow_queries) > 20:
            recommendations.append("High number of slow queries detected. Review database indexes and query optimization.")
        
        return recommendations

class PerformanceMonitor:
    """Monitor and report on system performance"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.request_count = 0
        self.response_times = []
        self.error_count = 0
        
    def record_request(self, response_time: float, success: bool = True):
        """Record a request for performance monitoring"""
        self.request_count += 1
        self.response_times.append(response_time)
        
        if not success:
            self.error_count += 1
        
        # Keep only last 1000 response times
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-1000:]
    
    def get_performance_report(self) -> Dict:
        """Generate performance report"""
        if not self.response_times:
            return {"message": "No performance data available"}
        
        uptime = datetime.now() - self.start_time
        avg_response_time = sum(self.response_times) / len(self.response_times)
        
        # Calculate percentiles
        sorted_times = sorted(self.response_times)
        p50 = sorted_times[len(sorted_times) // 2]
        p95 = sorted_times[int(len(sorted_times) * 0.95)]
        p99 = sorted_times[int(len(sorted_times) * 0.99)]
        
        return {
            'uptime': str(uptime),
            'total_requests': self.request_count,
            'error_rate': (self.error_count / self.request_count * 100) if self.request_count > 0 else 0,
            'response_times': {
                'average': round(avg_response_time, 3),
                'p50': round(p50, 3),
                'p95': round(p95, 3),
                'p99': round(p99, 3),
                'min': round(min(self.response_times), 3),
                'max': round(max(self.response_times), 3)
            },
            'requests_per_minute': round(self.request_count / (uptime.total_seconds() / 60), 2) if uptime.total_seconds() > 0 else 0
        }
