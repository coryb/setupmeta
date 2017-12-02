"""
Verify that ../examples/*/setup.py behave as expected
"""

import imp
import os
import re
import sys
import pytest

import setupmeta
import conftest


EXAMPLES = os.path.join(conftest.PROJECT, 'examples')
COMMANDS = 'explain entrypoints'.split()


def scenario_names():
    """ Available scenario names """
    names = []
    for name in os.listdir(EXAMPLES):
        if os.path.isdir(os.path.join(EXAMPLES, name)):
            names.append(name)
    return names


@pytest.fixture(params=scenario_names())
def scenario(request):
    """ Yield one test per scenario """
    yield request.param


def load_module(full_path):
    """ Load module pointed to by 'full_path' """
    fp = None
    try:
        folder = os.path.dirname(full_path)
        basename = os.path.basename(full_path).replace('.py', '')
        fp, pathname, description = imp.find_module(basename, [folder])
        imp.load_module(basename, fp, pathname, description)
    finally:
        if fp:
            fp.close()


def run(setup_py):
    """ Run 'setup_py' with 'command' """
    old_argv = sys.argv
    try:
        with conftest.capture_output() as logged:
            for command in COMMANDS:
                sys.argv = [setup_py, command]
                print("Replay: %s" % command)
                load_module(setup_py)
            return logged.to_string()
    finally:
        sys.argv = old_argv


def run_shell(*command):
    import subprocess
    p = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    output, error = p.communicate()
    return setupmeta.to_str(output) + setupmeta.to_str(error)


def test_scenario(scenario):
    """ Check that 'scenario' yields expected explain output """
    setup_py = os.path.join(EXAMPLES, scenario, 'setup.py')
    output = setupmeta.extract_list(run(setup_py))
    path = os.path.join(EXAMPLES, scenario, 'expected.txt')
    expected = setupmeta.load_list(path)
    assert expected == output


def chk(output, message):
    assert re.search(message, output), "'%s' not present in '%s'" % (message, setupmeta.short(output)) # noqa


def test_self():
    """ Test setupmeta's own setup.py """
    out = run_shell(
        sys.executable,
        os.path.join(conftest.PROJECT, 'setup.py'),
        'explain'
    )
    chk(out, "author:.+ Zoran Simic")
    chk(out, "description:.+ Stop copy-paste technology in setup.py")
    chk(out, "version:.+ [0-9]+\.[0-9]")
    chk(out, "url:.+ https://github.com/zsimic/setupmeta")
