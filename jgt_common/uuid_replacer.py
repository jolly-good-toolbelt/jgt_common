"""Replace UUIDs helper."""
import argparse
from itertools import count
import os
import re
import sys

from . import UUID_ISOLATED_RE


UUID_ISOLATED_MATCHER = re.compile(UUID_ISOLATED_RE)

UUID_REPLACEMENT_TEMPLATE = ",,UUID-{:03d},,"
"""
Template used to generate shorter version for a UUID.

Is expected to hold exaclty one numeric parameter substitution.
"""


class UUIDLineReplacer(object):
    """
    Track and Replace UUIDs on a line-by-line basis.

    Instances should be called with a line to process
    and will return the substituted line.

    When you are all done, if you want, you can call ``uuid_mappings``
    to get a list of the substitutions that were made.
    """

    def __init__(self, template=None):
        """
        Create a new UUID replacer.

        Args:
            template (str): A ``.format`` template to use for generating
                the UUID replacement values. It is expected to have a placeholder
                to format one numeric parameter.
        """

        self.count = count(start=1)
        self.uuid_map = {}
        self.template = template or UUID_REPLACEMENT_TEMPLATE

    def _add_uuid(self, uuid):
        if uuid in self.uuid_map:
            return
        self.uuid_map[uuid] = self.template.format(next(self.count))

    def __call__(self, line):
        """Replace all found UUIDs with markers."""
        uuids_found = set(UUID_ISOLATED_MATCHER.findall(line))
        for uuid in uuids_found:
            self._add_uuid(uuid)
        for uuid in uuids_found:
            line = line.replace(uuid, self.uuid_map[uuid])
        return line

    def uuid_mappings(self):
        """Return a list of lines of all the substitutions done."""
        return [
            "# {} -> {}\n".format(replacement, uuid)
            for uuid, replacement in sorted(
                self.uuid_map.items(), key=lambda item: item[1]
            )
        ]


def uuid_replace(src, dest, template=UUID_REPLACEMENT_TEMPLATE):
    """
    Replace UUIDs in all the lines in ``src`` and write to ``dest``.

    Args:
        src (file): a file opened for read
        dest (file): a file opened for write.

    After processing the contents of ``src`` into ``dest``, a glossary is then written
    to ``dest.``
    """

    replacer = UUIDLineReplacer(template=template)
    dest.writelines(map(replacer, src))
    dest.write("\n##########\n")
    dest.writelines(replacer.uuid_mappings())


def main():
    """Command-line interace for replacing UUIDs with placeholders."""
    description = (
        "Utility for replacing UUIDs in files with easier to read placeholders. "
        "The output file will have a glossary appended to it that shows "
        "each replacement string and the UUID it replaced. "
        "The template must have at most one format string replacement field "
        "which will be given a single numeric value. "
        "The environment variable UUID_TEMPLATE can be used to override the "
        "default value, and the `-t`/`-template` parameter can be used to "
        "overrride the environment variable."
    )
    parser = argparse.ArgumentParser(
        description=description, formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "input", nargs="?", type=argparse.FileType("r"), default=sys.stdin
    )
    parser.add_argument(
        "output", nargs="?", type=argparse.FileType("w"), default=sys.stdout
    )
    parser.add_argument(
        "--template",
        "-t",
        type=str,
        help="UUID replacement template",
        default=os.environ.get("UUID_TEMPLATE", UUID_REPLACEMENT_TEMPLATE),
    )

    args = parser.parse_args()

    uuid_replace(args.input, args.output, template=args.template)
