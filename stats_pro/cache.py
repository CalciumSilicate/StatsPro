# -*- coding: utf-8 -*-
"""缓存优化模块"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from functools import wraps
from threading import Lock
from typing import Any, Callable, Generic, TypeVar

from .constants import PLUGIN_ID

logger = logging.getLogger(PLUGIN_ID)

T = TypeVar("T")


@dataclass
class CacheEntry(Generic[T]):
    """缓存条目"""

    value: T
    expires_at: float
    created_at: float = field(default_factory=time.time)

    def is_expired(self) -> bool:
        """检查是否过期"""
        return time.time() > self.expires_at


class TTLCache(Generic[T]):
    """带 TTL 的缓存"""

    def __init__(self, default_ttl: float = 60.0, max_size: int = 1000):
        """
        初始化缓存

        Args:
            default_ttl: 默认过期时间（秒）
            max_size: 最大缓存条目数
        """
        self._cache: dict[str, CacheEntry[T]] = {}
        self._default_ttl = default_ttl
        self._max_size = max_size
        self._lock = Lock()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> T | None:
        """获取缓存值"""
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._misses += 1
                return None
            if entry.is_expired():
                del self._cache[key]
                self._misses += 1
                return None
            self._hits += 1
            return entry.value

    def set(self, key: str, value: T, ttl: float | None = None) -> None:
        """设置缓存值"""
        with self._lock:
            if len(self._cache) >= self._max_size:
                self._evict_expired()
                if len(self._cache) >= self._max_size:
                    self._evict_oldest()

            expires_at = time.time() + (ttl if ttl is not None else self._default_ttl)
            self._cache[key] = CacheEntry(value=value, expires_at=expires_at)

    def delete(self, key: str) -> bool:
        """删除缓存值"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        """清空所有缓存"""
        with self._lock:
            self._cache.clear()
            logger.debug("Cache cleared")

    def invalidate_pattern(self, pattern: str) -> int:
        """根据模式使缓存失效"""
        with self._lock:
            keys_to_delete = [
                key for key in self._cache if pattern in key
            ]
            for key in keys_to_delete:
                del self._cache[key]
            return len(keys_to_delete)

    def _evict_expired(self) -> int:
        """清除所有过期条目"""
        now = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.expires_at <= now
        ]
        for key in expired_keys:
            del self._cache[key]
        return len(expired_keys)

    def _evict_oldest(self) -> None:
        """清除最旧的条目"""
        if not self._cache:
            return
        oldest_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].created_at
        )
        del self._cache[oldest_key]

    @property
    def size(self) -> int:
        """当前缓存大小"""
        return len(self._cache)

    @property
    def stats(self) -> dict[str, Any]:
        """缓存统计信息"""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        return {
            "size": self.size,
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.1f}%",
        }


class StatsCache:
    """统计数据专用缓存"""

    def __init__(self, ttl: float = 30.0):
        """
        初始化统计缓存

        Args:
            ttl: 缓存过期时间（秒），默认30秒
        """
        self._player_cache: TTLCache[dict] = TTLCache(default_ttl=ttl)
        self._ranking_cache: TTLCache[dict] = TTLCache(default_ttl=ttl)
        self._sum_cache: TTLCache[dict] = TTLCache(default_ttl=ttl)
        self._ttl = ttl

    def get_player_stats(self, player: str) -> dict | None:
        """获取玩家统计缓存"""
        return self._player_cache.get(f"player:{player}")

    def set_player_stats(self, player: str, stats: dict) -> None:
        """设置玩家统计缓存"""
        self._player_cache.set(f"player:{player}", stats)

    def get_ranking(
        self,
        category: str | None = None,
        item: str | None = None,
        include_bots: bool = False,
    ) -> dict | None:
        """获取排行榜缓存"""
        key = f"rank:{category}:{item}:{include_bots}"
        return self._ranking_cache.get(key)

    def set_ranking(
        self,
        ranking: dict,
        category: str | None = None,
        item: str | None = None,
        include_bots: bool = False,
    ) -> None:
        """设置排行榜缓存"""
        key = f"rank:{category}:{item}:{include_bots}"
        self._ranking_cache.set(key, ranking)

    def get_sum(self, players_key: str) -> dict | None:
        """获取汇总缓存"""
        return self._sum_cache.get(f"sum:{players_key}")

    def set_sum(self, players_key: str, data: dict) -> None:
        """设置汇总缓存"""
        self._sum_cache.set(f"sum:{players_key}", data)

    def invalidate_player(self, player: str) -> None:
        """使玩家缓存失效"""
        self._player_cache.delete(f"player:{player}")
        self._ranking_cache.clear()
        self._sum_cache.clear()

    def invalidate_all(self) -> None:
        """使所有缓存失效"""
        self._player_cache.clear()
        self._ranking_cache.clear()
        self._sum_cache.clear()
        logger.debug("All stats cache invalidated")

    @property
    def stats(self) -> dict[str, dict]:
        """获取所有缓存的统计信息"""
        return {
            "player_cache": self._player_cache.stats,
            "ranking_cache": self._ranking_cache.stats,
            "sum_cache": self._sum_cache.stats,
        }


def cached(
    cache: TTLCache,
    key_func: Callable[..., str] | None = None,
    ttl: float | None = None,
) -> Callable:
    """
    缓存装饰器

    Args:
        cache: 缓存实例
        key_func: 生成缓存键的函数
        ttl: 自定义 TTL
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                key = f"{func.__name__}:{args}:{sorted(kwargs.items())}"

            cached_value = cache.get(key)
            if cached_value is not None:
                return cached_value

            result = func(*args, **kwargs)
            cache.set(key, result, ttl)
            return result

        wrapper.cache = cache  # type: ignore
        wrapper.invalidate = lambda: cache.clear()  # type: ignore
        return wrapper

    return decorator


# 全局缓存实例
_stats_cache: StatsCache | None = None


def get_stats_cache(ttl: float = 30.0) -> StatsCache:
    """获取全局统计缓存实例"""
    global _stats_cache
    if _stats_cache is None:
        _stats_cache = StatsCache(ttl=ttl)
    return _stats_cache
