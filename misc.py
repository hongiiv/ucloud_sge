#!/usr/bin/python
import logging, time
import subprocess
import threading
import datetime as dt
import os
import contextlib
import errno

def run(cmd, err=None, ok=None):
    """ Convenience method for executing a shell command. """
    # Predefine err and ok mesages to include the command being run
    if err is None:
        err = "---> PROBLEM"
    if ok is None:
        ok = "'%s' command OK" % cmd
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if process.returncode == 0:
        log.debug(ok)
        if stdout:
            return stdout
        else:
            return True
    else:
        log.error("%s, running command '%s' returned code '%s' and following stderr: '%s'" % (err, cmd, process.returncode, stderr))
        return False
