"""
Rate limiting utility for controlling user request frequency.
"""
import time
from collections import defaultdict, deque
from typing import Dict, Deque
from .config import settings
from .logger import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """Simple rate limiter for controlling request frequency per user."""
    
    def __init__(self):
        # Store request timestamps per user
        self.user_requests: Dict[int, Deque[float]] = defaultdict(deque)
        self.max_per_minute = settings.max_requests_per_minute
        self.max_per_hour = settings.max_requests_per_hour
    
    def is_allowed(self, user_id: int) -> tuple[bool, str]:
        """Check if user is allowed to make a request."""
        current_time = time.time()
        user_requests = self.user_requests[user_id]
        
        # Clean old requests (older than 1 hour)
        while user_requests and current_time - user_requests[0] > 3600:
            user_requests.popleft()
        
        # Count requests in the last minute and hour
        minute_ago = current_time - 60
        hour_ago = current_time - 3600
        
        recent_minute = sum(1 for req_time in user_requests if req_time > minute_ago)
        recent_hour = sum(1 for req_time in user_requests if req_time > hour_ago)
        
        # Check limits
        if recent_minute >= self.max_per_minute:
            return False, f"Превышен лимит запросов в минуту ({self.max_per_minute}). Попробуйте через минуту."
        
        if recent_hour >= self.max_per_hour:
            return False, f"Превышен лимит запросов в час ({self.max_per_hour}). Попробуйте через час."
        
        # Record this request
        user_requests.append(current_time)
        
        return True, ""
    
    def get_stats(self, user_id: int) -> Dict[str, int]:
        """Get current usage stats for user."""
        current_time = time.time()
        user_requests = self.user_requests[user_id]
        
        minute_ago = current_time - 60
        hour_ago = current_time - 3600
        
        recent_minute = sum(1 for req_time in user_requests if req_time > minute_ago)
        recent_hour = sum(1 for req_time in user_requests if req_time > hour_ago)
        
        return {
            "requests_last_minute": recent_minute,
            "requests_last_hour": recent_hour,
            "limit_per_minute": self.max_per_minute,
            "limit_per_hour": self.max_per_hour
        }


# Global rate limiter instance
rate_limiter = RateLimiter()