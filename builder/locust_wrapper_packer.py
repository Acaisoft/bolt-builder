import os
import shutil
import tempfile
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


class LocustWrapper:
    tar_basename = '.'

    _template_path: str
    _wrapper_template_url = 'git@bitbucket.org:acaisoft/bolt-locust-wrapper-template.git'
    _wrapper_template_branch = 'revival'
    _wrapper_repo = git.Repo

    def __init__(self):
        self._load_wrapper_template()

    def wrap(self, directory: str, no_cache=False):
        self._validate_repo(directory)
        if no_cache:
            self._reload_wrapper_template()
        copy_tree(self._template_path, directory)

        requirements_txt_path = os.path.join(directory, 'requirements.txt')
        if not os.path.exists(requirements_txt_path):
            open(requirements_txt_path, 'w').close()

    def _validate_repo(self, direcotry):
        module_path = os.path.join(direcotry, 'tests')

        if not os.path.exists(os.path.join(module_path, '__init__.py')):
            raise ValidationError('"tests" directory in repository is not a python module. Missing "__init__.py" file.')

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
