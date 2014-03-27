import logging
import os
import re
from subprocess import Popen, PIPE

from aitools.errors import AiToolsGitError

GITBINPATH = "/usr/bin/git"

class GitClient(object):
    def __init__(self):
        pass

    def get_head(self, repository_path):
        out, returncode = self.__exec(["rev-parse", "HEAD"], gitdir=repository_path)
        return out.strip()

    def __exec(self, args, gitdir=None, gitworkingtree=None):
        env = os.environ.copy()
        if gitdir is not None:
            logging.debug("Setting GIT_DIR to %s" % gitdir)
            env['GIT_DIR'] = gitdir
        if gitworkingtree is not None:
            logging.debug("Setting GIT_WORK_TREE to %s" % gitworkingtree)
            env['GIT_WORK_TREE'] = gitworkingtree
        args = [GITBINPATH] + args
        logging.debug("Executing git %s" % args)
        git = Popen(args, stdout = PIPE, stderr=PIPE, env=env)
        (details, err)  = git.communicate()
        returncode = git.returncode
        if returncode != 0:
            raise AiToolsGitError("Couln't execute git %s (%s)" % \
                (args, err.strip()))
        return (details, returncode)
