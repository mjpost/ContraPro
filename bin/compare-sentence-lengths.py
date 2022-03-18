#!/usr/bin/env python3

"""
Compares the number of sentence pairs that have the same length
when split on <eos>.
"""

import sys


def main(args):
    for lineno, line in enumerate(sys.stdin):
        fields = line.rstrip().split("\t")
        str1, str2 = fields[args.col1], fields[args.col2]

        if len(str1.split(args.separator)) != len(str2.split(args.separator)):
            print(line, end="")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("col1", type=int)
    parser.add_argument("col2", type=int)
    parser.add_argument("--separator", default="\t")
    args = parser.parse_args()

    main(args)
