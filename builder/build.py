import tempfile
import uuid
import os
import logging
import sys
import git

from cache import Cache

from google_cloud_build import GoogleCloudBuild
from locust_wrapper_packer import LocustWrapperPacker
from execution_stage_log import send_stage_log

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

logger = logging.getLogger(__name__)

cache = Cache()


def get_docker_image_destination(tenant_id: str, project_id: str):
    name = str(uuid.uuid4())
    return '{base_registry}:tenants-{tenant}-projects-{project}-{name}'.format(
        base_registry='eu.gcr.io/acai-bolt/bolt-deployer-builds-local'.rstrip('/'),
        tenant=tenant_id,
        project=project_id,
        name=name,
    )


def write_output(docker_image):
    with open('/tmp/image.txt', 'w+') as file:
        file.write(docker_image)


send_stage_log('SUCCEEDED', 'start')

repo_url = os.environ.get('REPOSITORY_URL')
branch = os.environ.get('BRANCH', 'master')
repo_path = tempfile.mkdtemp()
tenant_id = os.environ.get('TENANT_ID')
project_id = os.environ.get('PROJECT_ID')

send_stage_log('PENDING', stage='downloading_source')
logger.info(f'Cloning repository {repo_url}...')
repo = git.Repo.clone_from(repo_url, repo_path, branch=branch, depth=1)
send_stage_log('SUCCEEDED', 'downloading_source')
logger.info(f'Repository cloned to {repo_path}')
head_sha = repo.head.object.hexsha

send_stage_log('PENDING', 'image_preparation')
if not int(os.environ.get('NO_CACHE')):
    docker_image = cache.get_docker_image_by_sha(tenant_id, project_id, head_sha)
    if docker_image:
        logger.info(f'Found image in cache: {docker_image}')
        write_output(docker_image)
        send_stage_log('SUCCEEDED', 'image_preparation')
        exit(0)

logger.info('Wrapping repository')
wrapper = LocustWrapperPacker()
wrapper.wrap(repo_path)
logger.info('Repository wrapped')

destination = get_docker_image_destination(tenant_id, project_id)
logger.info(f'Starting to build image {destination}')
google_cloud_build = GoogleCloudBuild()
google_cloud_build.build(repo_path, destination)
logger.info('Image built')

cache.set_docker_image_by_sha(tenant_id, project_id, head_sha, destination)
logger.info(f'Written image to cache: {destination}')

write_output(destination)
send_stage_log('SUCCEEDED', 'image_preparation')
