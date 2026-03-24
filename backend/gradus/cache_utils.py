"""
Cache utilities for Gradus application.
Implements intelligent caching for expensive queries and API responses.
"""

from functools import wraps
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.conf import settings
from django.http import QueryDict
import hashlib
import json


def cache_key_from_request(prefix, request, include_params=True):
    """
    Generate a unique cache key from request context.

    Args:
        prefix: Cache key prefix (e.g., 'classroom_list')
        request: Django request object
        include_params: Whether to include query parameters in key

    Returns:
        Unique cache key string
    """
    user_id = str(request.user.id) if request.user.is_authenticated else "anon"
    base_key = f"{prefix}:user_{user_id}"

    if include_params and request.GET:
        # Sort query params for consistent hashing
        params = dict(sorted(request.GET.items()))
        params_str = json.dumps(params, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()
        return f"{base_key}:params_{params_hash}"

    return base_key


def invalidate_cache_pattern(pattern):
    """
    Invalidate all cache entries matching a pattern.
    This is a helper for cache invalidation on data changes.

    Args:
        pattern: String pattern to search for in cache keys
    """
    # Note: Django's database cache backend doesn't support pattern deletion
    # For production, use Redis with django-redis for better control
    # This is a placeholder for explicit invalidation calls
    pass


def cache_get_queryset(timeout=None):
    """
    Decorator for caching expensive queryset list endpoints.
    Caches based on the entire request (user + query params).

    Usage:
        @cache_get_queryset(timeout=3600)
        def get_queryset(self):
            return MyModel.objects.all()

    Args:
        timeout: Cache timeout in seconds (uses settings default if None)
    """
    if timeout is None:
        timeout = getattr(settings, "CACHE_TIMEOUT_CLASSROOM", 3600)

    def decorator(func):
        @wraps(func)
        def wrapper(self):
            # Skip caching for POST/PUT/DELETE methods
            if self.request.method != "GET":
                return func(self)

            # Generate cache key from request
            cache_key = cache_key_from_request(
                f"{self.__class__.__name__}:queryset", self.request, include_params=True
            )

            # Try to get from cache
            cached = cache.get(cache_key)
            if cached is not None:
                return cached

            # Execute function and cache result
            queryset = func(self)
            # Convert queryset to list for caching (querysets can't be pickled)
            try:
                list_data = list(queryset)
                cache.set(cache_key, list_data, timeout)
                return queryset  # Return original queryset
            except Exception:
                # If caching fails, just return uncached queryset
                return queryset

        return wrapper

    return decorator


def cache_api_response(timeout=None, key_func=None):
    """
    Decorator for caching API response data.

    Usage:
        @cache_api_response(timeout=1800)
        def retrieve(self, request, *args, **kwargs):
            # View code
            return Response(data)

    Args:
        timeout: Cache timeout in seconds
        key_func: Custom function to generate cache key
    """
    if timeout is None:
        timeout = 3600

    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            # Skip caching for non-safe methods
            if request.method != "GET":
                return func(self, request, *args, **kwargs)

            # Generate or use custom cache key
            if key_func:
                cache_key = key_func(self, request, args, kwargs)
            else:
                cache_key = cache_key_from_request(
                    f"{self.__class__.__name__}:response", request, include_params=True
                )

            # Try to get cached response
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                # Return cached data wrapped in Response
                from rest_framework.response import Response

                return Response(cached_data)

            # Execute view and cache result
            response = func(self, request, *args, **kwargs)

            # Cache response data if successful
            if hasattr(response, "data") and 200 <= response.status_code < 300:
                cache.set(cache_key, response.data, timeout)

            return response

        return wrapper

    return decorator


def clear_classroom_cache(classroom_id):
    """
    Clear all caches related to a specific classroom.
    Call this when classroom is updated.

    Args:
        classroom_id: UUID of the classroom
    """
    patterns = [
        f"ClassroomListCreateView:queryset:user_",
        f"ClassroomDetailView:response:user_",
        f"ClassroomGradebookAPIView:response:user_",
        f"TaskListCreateAPIView:queryset:user_",
    ]

    # For database cache, we need explicit key deletion
    # In production, switch to redis for pattern-based deletion
    for pattern in patterns:
        # Delete specific variations
        for component in ["theory", "lab", ""]:
            key = f"{pattern}{classroom_id}:{component}"
            cache.delete(key)


def clear_task_cache(task_id, classroom_id=None):
    """
    Clear caches related to a specific task or classroom tasks.

    Args:
        task_id: UUID of the task (optional)
        classroom_id: UUID of classroom (if task_id not provided)
    """
    if task_id:
        cache.delete(f"TaskListCreateAPIView:queryset:task_{task_id}")
        cache.delete(f"TaskRetrieveUpdateDestroyAPIView:response:task_{task_id}")

    if classroom_id:
        clear_classroom_cache(classroom_id)


def get_or_set_cache(key, callable_func, timeout=None):
    """
    Convenience method for get_or_set pattern.

    Args:
        key: Cache key
        callable_func: Function to call if cache miss
        timeout: Cache timeout in seconds

    Returns:
        Cached or freshly computed value
    """
    if timeout is None:
        timeout = DEFAULT_TIMEOUT

    value = cache.get(key)
    if value is None:
        value = callable_func()
        cache.set(key, value, timeout)

    return value
