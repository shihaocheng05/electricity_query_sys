# 缓存工具（验证码存储、用电数据缓存）
import redis
from flask import current_app
import random
import string

class RedisClient:
    """Redis客户端封装"""
    _instance = None
    _client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def init_app(self, app):
        """初始化Redis连接"""
        try:
            self._client = redis.Redis(
                host=app.config.get('REDIS_HOST', 'localhost'),
                port=app.config.get('REDIS_PORT', 6379),
                db=app.config.get('REDIS_DB', 0),
                decode_responses=True,
                password=app.config.get('REDIS_PASSWORD', None)
            )
            # 测试连接
            self._client.ping()
            app.logger.info("Redis连接成功")
        except Exception as e:
            app.logger.warning(f"Redis连接失败，将使用内存缓存: {str(e)}")
            self._client = None
    
    @property
    def client(self):
        return self._client


# 内存缓存（当Redis不可用时使用）
_memory_cache = {}

def get_redis_client():
    """获取Redis客户端"""
    redis_client = RedisClient()
    return redis_client.client


def set_cache(key: str, value: str, expire: int = 300):
    """
    设置缓存
    :param key: 键
    :param value: 值
    :param expire: 过期时间（秒），默认5分钟
    """
    client = get_redis_client()
    try:
        if client:
            client.setex(key, expire, value)
        else:
            # 使用内存缓存
            import time
            _memory_cache[key] = (value, time.time() + expire)
    except Exception as e:
        current_app.logger.error(f"设置缓存失败: {str(e)}")
        # 降级到内存缓存
        import time
        _memory_cache[key] = (value, time.time() + expire)


def get_cache(key: str):
    """
    获取缓存
    :param key: 键
    :return: 值，不存在返回None
    """
    client = get_redis_client()
    try:
        if client:
            return client.get(key)
        else:
            # 使用内存缓存
            import time
            if key in _memory_cache:
                value, expire_time = _memory_cache[key]
                if time.time() < expire_time:
                    return value
                else:
                    del _memory_cache[key]
            return None
    except Exception as e:
        current_app.logger.error(f"获取缓存失败: {str(e)}")
        return None


def delete_cache(key: str):
    """
    删除缓存
    :param key: 键
    """
    client = get_redis_client()
    try:
        if client:
            client.delete(key)
        else:
            if key in _memory_cache:
                del _memory_cache[key]
    except Exception as e:
        current_app.logger.error(f"删除缓存失败: {str(e)}")


def generate_verification_code(length: int = 6) -> str:
    """
    生成验证码
    :param length: 验证码长度，默认6位
    :return: 验证码字符串
    """
    return ''.join(random.choices(string.digits, k=length))


def save_verification_code(email: str, code: str, expire: int = 300):
    """
    保存验证码
    :param email: 邮箱
    :param code: 验证码
    :param expire: 过期时间（秒），默认5分钟
    """
    key = f"verification_code:{email}"
    set_cache(key, code, expire)


def verify_code(email: str, code: str) -> bool:
    """
    验证验证码
    :param email: 邮箱
    :param code: 用户输入的验证码
    :return: 验证结果
    """
    key = f"verification_code:{email}"
    saved_code = get_cache(key)
    
    if saved_code is None:
        return False
    
    if saved_code == code:
        # 验证成功后删除验证码（一次性使用）
        delete_cache(key)
        return True
    
    return False
