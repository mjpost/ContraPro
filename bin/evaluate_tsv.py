#!/usr/bin/env python3

import sys

from sacremoses import MosesTokenizer


def main(args):
    tok = MosesTokenizer(lang="de")

    correct = 0
    total = 0
    for lineno, line in enumerate(sys.stdin, 1):
        fields = line.rstrip().split("\t")
        if len(fields) == 7:
            fields.pop(0)
        dist, label, pronoun, source, reference, system = fields
        pronoun = pronoun.lower()

        if label != "correct":
            continue

        if int(dist) < args.distance[0] or int(dist) > args.distance[1]:
            continue

        if args.pronouns and "all" not in args.pronouns and pronoun not in args.pronouns:
            continue

        output = tok.tokenize(system.split(args.separator)[-1], return_str=True)

        total += 1
        is_correct = pronoun in output.lower().split()
        if is_correct:
            correct += 1

        if args.debug:
            print(lineno, is_correct, pronoun, "in", output, sep="\t", file=sys.stderr)

    # print(f"{correct}/{total}={100*correct/total:.1f}")
    print(f"{correct} {total} {100*correct/total:.1f}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("infile", nargs="?", type=argparse.FileType("r"), default=sys.stdin)
    parser.add_argument("--separator", default="<eos>")
    parser.add_argument("--distance", "-d", nargs=2, default=[0, 1000000], type=int)
    parser.add_argument("--pronouns", "-p", nargs="+", default=[], choices="all er es sie il ils elle elles".split())
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    main(args)
