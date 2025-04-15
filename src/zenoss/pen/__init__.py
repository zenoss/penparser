from __future__ import absolute_import, print_function

import argparse
import io
import json
import os
import sys

try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen

try:
    import pathlib
except ImportError:
    import pathlib2 as pathlib


_zenhome = pathlib.Path(os.environ.get("ZENHOME"))

IANA_URL = "https://www.iana.org/assignments/enterprise-numbers.txt"
IANA_PREFIX = ".1.3.6.1.4.1"
PEN_ORG_FILE = _zenhome / "share" / "iana" / "pen_map.json"


def parse_pen_data():
    args = _get_cli_args()
    source = args.source
    pathname = args.path
    if not pathname.parent.exists():
        print(
            "Directory not found: {}".format(pathname.parent), file=sys.stderr
        )
        sys.exit(1)
    stdout = bool(pathname.is_dir())

    if not source.startswith("http"):
        source = "file:{}".format(source)

    try:
        instream = urlopen(source)
        iana_content = instream.read().decode(sys.getdefaultencoding())
        instream.close()
    except IOError:
        print("Unable to retrieve OIDs", file=sys.stderr)
        print("  - {}".format(source), file=sys.stderr)
        sys.exit(1)

    pens = _parse_pens(iana_content)
    if stdout:
        _write(pens, sys.stdout)
    else:
        with io.open(pathname.as_posix(), "wb") as fo:
            _write(pens, fo)

    print("IANA Private Enterprise Number OID mapping written to file.")
    print("  %s" % pathname)


def _write(pens, fp):
    json.dump(pens, fp, ensure_ascii=False, indent=4, separators=(u",", u": "))


def _get_cli_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-o",
        dest="path",
        type=pathlib.Path,
        default=PEN_ORG_FILE,
        help="Path to the output file",
    )
    parser.add_argument(
        "-s",
        dest="source",
        default=IANA_URL,
        help="Private Enterprise Numbers source file/URL",
    )
    return parser.parse_args()


def _parse_pens(data):
    register = {}
    lines = iter(data.splitlines())

    while True:
        try:
            line = lines.next().strip()
            if not line.isdigit():
                continue
            number = int(line)
            org = lines.next().strip()

            # skip the 'contact' and 'email' lines
            lines.next()
            lines.next()

            if org in ("Unassigned", "Reserved", "none"):
                continue

            register["{}.{}".format(IANA_PREFIX, number)] = org
        except StopIteration:
            break

    return register
