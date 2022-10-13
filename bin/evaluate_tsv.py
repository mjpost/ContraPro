#!/usr/bin/env python3

import sys

from sacremoses import MosesTokenizer


def main(args):
    tok = MosesTokenizer(lang="de")

    correct = 0
    total = 0
    for lineno, line in enumerate(sys.stdin, 1):
        target_index, dist, label, pronoun, source, reference, system = line.rstrip().split("\t")
        pronoun = pronoun.lower()

        if label != "correct":
            continue

        if int(dist) < args.distance[0] or int(dist) > args.distance[1]:
            continue

        if args.pronouns and "all" not in args.pronouns and pronoun not in args.pronouns:
            continue

        output = tok.tokenize(system.split(args.separator)[-1], return_str=True)

        total += 1
        if pronoun in output.lower().split():
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
    parser.add_argument("--separator", default="<eos>")
    parser.add_argument("--distance", "-d", nargs=2, default=[0, 100], type=int)
    parser.add_argument("--pronouns", "-p", nargs="+", default=[], choices="all er es sie il ils elle elles".split())
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    main(args)
