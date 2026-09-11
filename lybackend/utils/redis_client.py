import redis
import json
from config import Config

class RedisClient:
    """Redis客户端封装"""
    
    def __init__(self):
        self.client = redis.Redis(
            host=Config.REDIS_HOST,
            port=Config.REDIS_PORT,
            db=Config.REDIS_DB,
            password=Config.REDIS_PASSWORD,
            decode_responses=True
        )
    
    def get(self, key):
        """获取缓存"""
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Redis get error: {e}")
            return None
    
    def set(self, key, value, expire=3600):
        """设置缓存"""
        try:
            self.client.setex(key, expire, json.dumps(value, ensure_ascii=False))
            return True
        except Exception as e:
            print(f"Redis set error: {e}")
            return False
    
    def delete(self, key):
        """删除缓存"""
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            print(f"Redis delete error: {e}")
            return False
    
    def exists(self, key):
        """检查key是否存在"""
        try:
            return self.client.exists(key)
        except Exception as e:
            print(f"Redis exists error: {e}")
            return False
    
    def clear_pattern(self, pattern):
        """清除匹配模式的所有key"""
        try:
            keys = self.client.keys(pattern)
            if keys:
                self.client.delete(*keys)
            return True
        except Exception as e:
            print(f"Redis clear pattern error: {e}")
            return False

# 全局Redis客户端实例
redis_client = RedisClient()
