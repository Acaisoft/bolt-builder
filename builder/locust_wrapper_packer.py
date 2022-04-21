import os
import shutil
import tarfile
import tempfile
from binascii import hexlify
from distutils.dir_util import copy_tree

import git

from dataclasses import dataclass


class ValidationError(Exception):
    ...


@dataclass
class RepoTar:
    basename: str
    path: str

    def clear(self):
        if os.path.exists(self.path):
            os.remove(self.path)


class LocustWrapperPacker:
    tar_basename = '.'

    _template_path: str
    _wrapper_template_url = 'git@bitbucket.org:acaisoft/bolt-locust-wrapper-template.git'
    _wrapper_template_branch = 'revival'
    _wrapper_repo = git.Repo

    def __init__(self):
        self._load_wrapper_template()

    def wrap_and_pack(self, directory_to_wrap: str, no_cache: bool = False) -> RepoTar:
        """
        :param directory_to_wrap: Path to repository
        :return: Path to gzipped wrapped repository
        """
        self.wrap(directory_to_wrap, no_cache=no_cache)
        return self.pack(directory_to_wrap)

    def wrap(self, directory: str, no_cache=False):
        self._validate_repo(directory)
        if no_cache:
            self._reload_wrapper_template()
        copy_tree(self._template_path, directory)

        requirements_txt_path = os.path.join(directory, 'requirements.txt')
        if not os.path.exists(requirements_txt_path):
            open(requirements_txt_path, 'w').close()

    def pack(self, directory: str) -> RepoTar:
        tar_path = self._create_empty_tar_file()
        with tarfile.open(tar_path, 'w:gz') as tar:
            tar.add(directory, arcname=self.tar_basename)
        return RepoTar(
            basename=self.tar_basename,
            path=tar_path,
        )

    def _validate_repo(self, direcotry):
        module_path = os.path.join(direcotry, 'tests')

        if not os.path.exists(os.path.join(module_path, '__init__.py')):
            raise ValidationError('"tests" directory in repository is not a python module. Missing "__init__.py" file.')

    def _create_empty_tar_file(self) -> str:
        tmp_dir = tempfile.mkdtemp()
        tar_name = f'kaniko_context_{hexlify(os.urandom(10)).decode()}.gz'
        tar_path = os.path.join(tmp_dir, tar_name)
        open(tar_path, 'w').close()
        return tar_path

    def _load_wrapper_template(self):
        template_path = tempfile.mkdtemp()
        self._wrapper_repo = git.Repo.clone_from(
            self._wrapper_template_url,
            template_path,
            branch=self._wrapper_template_branch,
            depth=1,
        )

        shutil.rmtree(os.path.join(template_path, '.git'))

        self._template_path = template_path

    def _reload_wrapper_template(self):
        old_template_path = self._template_path
        self._load_wrapper_template()
        shutil.rmtree(old_template_path)
