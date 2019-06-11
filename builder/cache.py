import os
import logging

from typing import NoReturn
from typing import Optional
from typing import Tuple

import redis

logger = logging.getLogger(__name__)


class Cache:
    DOCKER_IMAGE_PREFIX = 'docker-images'

    def __init__(self, redis_url: str = os.environ['REDIS_URL']):
        self.redis_cli = redis.Redis.from_url(redis_url)

    def get_docker_image_by_sha(self, tenant_id: str, project_id: str, hexsha: str) -> Optional[str]:
        key = self.key_docker_image_by_sha(tenant_id, project_id, hexsha)
        out = self.redis_cli.get(key)
        if out is not None:
            out = out.decode()
        return out

    def set_docker_image_by_sha(self, tenant_id: str, project_id: str, hexsha: str, docker_image: str) -> NoReturn:
        key = self.key_docker_image_by_sha(tenant_id, project_id, hexsha)
        self.redis_cli.set(key, docker_image)
        logger.debug(f'Set redis key. key={key}, value={docker_image}')

    def delete_docker_image_by_sha(self, tenant_id: str, project_id: str, hexsha: str) -> NoReturn:
        key = self.key_docker_image_by_sha(tenant_id, project_id, hexsha)
        self.redis_cli.delete(key)
        logger.debug(f'Deleted a key from redis. key={key}')

    def get_docker_image_keys_by_project(self, tenant_id: str, project_id: str) -> Tuple[str]:
        key = self.key(self.DOCKER_IMAGE_PREFIX, tenant_id, project_id, '*')
        return tuple(b.decode() for b in self.redis_cli.keys(key))

    def delete_keys(self, *keys: str):
        self.redis_cli.delete(*keys)
        logger.debug(f'Deleted keys from redis. key={keys}')

    def get_keys(self, *keys: str) -> Tuple[str]:
        return tuple(b.decode() for b in self.redis_cli.mget(keys) if b is not None)

    def key_docker_image_by_sha(self, tenant_id: str, project_id: str, hexsha: str):
        return self.key(self.DOCKER_IMAGE_PREFIX, tenant_id, project_id, hexsha)

    def key(self, *args: str) -> str:
        return ':'.join(args)

    def ping(self):
        return self.redis_cli.ping()
