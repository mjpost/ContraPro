#!/usr/bin/env python3

import sys

from sacremoses import MosesTokenizer


def main(args):
    tok = MosesTokenizer(lang=args.lang)

    correct = 0
    total = 0
    for lineno, line in enumerate(sys.stdin, 1):
        fields = line.rstrip().split("\t")
        payload_field = -1
        if len(fields) == 6:
            dist, label, pronoun, source, reference, system = fields
        elif len(fields) == 7:
            payload_field, dist, label, pronoun, source, reference, system = fields
            payload_field = int(payload_field)
        pronoun = pronoun.lower()

        if label != "correct":
            continue

        if int(dist) < args.distance[0] or int(dist) > args.distance[1]:
            continue

        if args.pronouns and "all" not in args.pronouns and pronoun not in args.pronouns:
            continue

        # hack for FR, Moses tokenizer doesn't split e.g., "pouvent-elles"
        if args.lang == "fr":
            output = system.replace("-", " - ")

        if args.proportional:
            # find out what pct the source payload takes in source
            payload_pct = len(source.split(args.separator)[-1].split()) / len(source.split())
            # use that to find target range (with a bit of margin)
            output_len = len(system.split())
            num_output_tokens = int(output_len * payload_pct * args.proportional)
            output = tok.tokenize(" ".join(system.split()[-num_output_tokens:]), return_str=True)
            # print(f"Using {payload_pct*100:.1f}% of output ({num_output_tokens} / {output_len})")
            # print("->", output)
        else:
            # silently skip imbalanced outputs
            try:
                output = tok.tokenize(system.split(args.separator)[payload_field], return_str=True)
            except IndexError:
                output = ""

        total += 1
        is_correct = pronoun in output.lower().split()
        if is_correct:
            correct += 1

        if args.debug:
            print(lineno, dist, is_correct, pronoun, source, system, reference, sep="\t", file=sys.stderr)

    # print(f"{correct}/{total}={100*correct/total:.1f}")
    if args.verbose:
        print(f"{correct} {total} {100*correct/total:.1f}")
    else:
        print(f"{100*correct/total:.1f}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("infile", nargs="?", type=argparse.FileType("r"), default=sys.stdin)
    parser.add_argument("--lang", "-l", default="de")
    parser.add_argument("--proportional", type=float, default=None, help="Instead of splitting on separator, use sentence proportions")
    parser.add_argument("--separator", default="<eos>")
    parser.add_argument("--distance", "-d", nargs=2, default=[0, 1000000], type=int)
    parser.add_argument("--pronouns", "-p", nargs="+", default=[], choices="all er es sie il ils elle elles".split())
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    main(args)
