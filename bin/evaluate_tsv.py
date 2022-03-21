#!/usr/bin/env python3

import sys

from sacremoses import MosesTokenizer


def main(args):
    tok = MosesTokenizer(lang="de")

    correct = 0
    total = 0
    for lineno, line in enumerate(sys.stdin, 1):
        dist, label, pronoun, source, reference, system = line.rstrip().split("\t")

        if label != "correct":
            continue
        if args.distance is not None and args.distance != int(dist):
            continue
        if args.pronoun and pronoun not in args.pronoun:
            continue

        output = tok.tokenize(system.split(args.separator)[-1], return_str=True)

        total += 1
        if pronoun.lower() in output.lower().split():
            if args.debug:
                print(lineno, pronoun, "in", output, file=sys.stderr)
            correct += 1
        # else:
        #     print(lineno, "NO", pronoun, "in", output, file=sys.stderr)

    # print(f"{correct}/{total}={100*correct/total:.1f}")
    print(f"{100*correct/total:.1f}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("infile", nargs="?", type=argparse.FileType("r"), default=sys.stdin)
    parser.add_argument("--separator", default=" <eos> ")
    parser.add_argument("--distance", "-d", type=int)
    parser.add_argument("--pronoun", "-p", nargs="+", default=[], choices="er es sie".split())
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    main(args)
