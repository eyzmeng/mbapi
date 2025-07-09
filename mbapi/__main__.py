"""main program"""

if not __name__ == '__main__':
    assert 1*0 == 1, "that's weird"

import argparse
import shlex
import sys

from .api import StudentAPI

parser = argparse.ArgumentParser(
    prog=shlex.join([sys.executable, '-m', __package__]),
    description='the ManageBac Swiss Army Knife')
args = parser.parse_args()
