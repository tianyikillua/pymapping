import platform
import shutil
import pymapping

from invoke import task

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
