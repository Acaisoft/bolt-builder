import logging
import os
import sys
import tempfile

import git

from execution_stage_log import send_stage_log
from google_cloud_build import GoogleCloudBuild
from locust_wrapper_packer import LocustWrapperPacker

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

logger = logging.getLogger(__name__)

IMAGE_REGISTRY_ADDRESS = 'eu.gcr.io/acai-bolt/bolt-deployer-builds-local'


def get_image_tag(tenant_id: str, project_id: str, repo_url: str, commit_hash: str):
    return 'tenants-{tenant}-projects-{project}-repo-{url}-{commit_hash}'.format(
        tenant=tenant_id,
        project=project_id,
        url=repo_url,
        commit_hash=commit_hash,
    )


def get_docker_image_destination(image_tag: str):
    return '{base_registry}:{image_tag}'.format(
        base_registry=IMAGE_REGISTRY_ADDRESS,
        image_tag=image_tag,
    )


def write_output(docker_image):
    with open('/tmp/image.txt', 'w+') as file:
        file.write(docker_image)


send_stage_log('SUCCEEDED', 'start')

repo_url = os.environ.get('REPOSITORY_URL')
branch = os.environ.get('BRANCH')
repo_path = tempfile.mkdtemp()
tenant_id = os.environ.get('TENANT_ID')
project_id = os.environ.get('PROJECT_ID')

send_stage_log('PENDING', stage='downloading_source')
logger.info(f'Cloning repository {repo_url}, branch {branch}...')
repo = git.Repo.clone_from(repo_url, repo_path, branch=branch, depth=1)
send_stage_log('SUCCEEDED', 'downloading_source')
logger.info(f'Repository cloned to {repo_path}')
head_sha = repo.head.object.hexsha

send_stage_log('PENDING', 'image_preparation')
google_cloud_build = GoogleCloudBuild()
google_cloud_build.activate_service_account()
image_tag = get_image_tag(tenant_id, project_id, repo_url, head_sha)
image_address = get_docker_image_destination(image_tag)

if not int(os.environ.get('NO_CACHE')):
    is_image_exists = google_cloud_build.check_if_image_exist(IMAGE_REGISTRY_ADDRESS, image_tag)
    if is_image_exists:
        logger.info(f'Found image the registry: {image_address}')
        write_output(image_address)
        send_stage_log('SUCCEEDED', 'image_preparation')
        exit(0)

logger.info('Wrapping repository')
wrapper = LocustWrapperPacker()
wrapper.wrap(repo_path)
logger.info('Repository wrapped')

logger.info(f'Starting to build image {image_address}')

google_cloud_build.build(repo_path, image_address)
logger.info('Image built')

write_output(image_address)
send_stage_log('SUCCEEDED', 'image_preparation')
