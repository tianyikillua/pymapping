import platform
import shutil

from invoke import task

import pymapping

VERSION = pymapping.__version__


@task
def build(c):
    print(f"Building v{VERSION}...")
    shutil.rmtree("dist", ignore_errors=True)
    if platform.system() == "Windows":
        python = "python"
    else:
        python = "python3"
    c.run(f"{python} setup.py sdist")
    c.run(f"{python} setup.py bdist_wheel")


@task
def tag(c):
    print(f"Tagging v{VERSION}...")
    c.run(f"git tag v{VERSION}")
    c.run("git push --tags")


@task
def upload(c):
    print("Uploading wheels from dist/* to PyPI...")
    c.run("twine upload dist/*")


@task
def docs(c):
    print("Building docs...")
    c.run("sphinx-build docs docs/_build")


@task
def format(c):
    c.run("isort -rc .")
    c.run("black .")
