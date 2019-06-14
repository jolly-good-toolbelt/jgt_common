import os

from qecommon_tools import get_file_contents
from qecommon_tools.uuid_replacer import uuid_replace

HERE = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(HERE, 'uuid-only-lines.input')
EXPECTED_OUTPUT_FILE = os.path.join(HERE, 'uuid-only-lines.output')


def test_uuid_replacer(tmpdir):
    testoutput_filename = tmpdir / 'test.output'
    with testoutput_filename.open('w') as testoutput, open(INPUT_FILE, 'r') as testinput:
        uuid_replace(testinput, testoutput)

    assert get_file_contents(EXPECTED_OUTPUT_FILE) == get_file_contents(str(testoutput_filename))
