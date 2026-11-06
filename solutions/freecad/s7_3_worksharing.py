"""Exercise 7.3: the IFC model under Git. These are the command-line steps of the lesson, run from Python.

    git init tb01_repo
    copy tb01.ifc (exported after section 1) into it, git add tb01.ifc, git commit -m "Levels and grid"
    export tb01.ifc again after section 2,          git commit -am "Columns, core walls, slab and beams"
"""
import os
import shutil
import subprocess

try:
    from fc_common import out
except ImportError:                     # plain Python, outside FreeCAD
    def out(name):
        return os.path.join(os.environ.get("FC_OUT", "/tmp/fc_out"), name)


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True, text=True).stdout


def build():
    repo = out("tb01_repo")
    shutil.rmtree(repo, ignore_errors=True)
    os.makedirs(repo)
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "TB-01 Learner")             # once per computer: git config --global ...
    git(repo, "config", "user.email", "learner@example.com")
    shutil.copy(out("tb01_s1.ifc"), os.path.join(repo, "tb01.ifc"))
    git(repo, "add", "tb01.ifc")
    git(repo, "commit", "-q", "-m", "Levels and grid")
    shutil.copy(out("tb01_s2.ifc"), os.path.join(repo, "tb01.ifc"))
    git(repo, "commit", "-q", "-am", "Columns, core walls, slab and beams")
    print(git(repo, "log", "--oneline"))
    return repo


if __name__ == "__main__":
    build()
