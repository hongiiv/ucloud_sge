#!/usr/bin/python
import pexpect
import sys
import time
import os

foo = pexpect.spawn('ssh root@localhost uname -a')
foo.expect('.ssword:*')
foo.sendline('bio1234!')
foo.interact()
