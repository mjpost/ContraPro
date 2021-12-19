#!/usr/bin/env python

import os
import re
import sys
import json

# sub noWS{
#  my $string = $_[0];
#  return $string =~ s/\s\t\n//g;
# }


def noWS(s):
    return re.sub(r"\s\t\n", "", s)


def get_context(is_too_long, lineno, doc):
    context_line = lineno - 1

    source_context = []
    target_context = []
    while context_line >= 1:
        source_context.insert(0, doc[0][context_line-1])
        target_context.insert(0, doc[1][context_line-1])
        if is_too_long(source_context):
            source_context.pop(0)
            target_context.pop(0)
            break

        context_line -= 1

    return source_context, target_context


def stripread(fh):
    lines = []
    for line in fh:
        lines.append(line.rstrip("\r\n"))
    return lines


def main(args):
    spm = None
    if args.spm:
        from sentencepiece import SentencePieceProcessor
        spm = SentencePieceProcessor(model_file=args.spm)

    filenames = {}
    for subfolder in os.listdir(args.dir):
        for file_name in os.listdir(os.path.join(args.dir, subfolder)):
            if file_name.endswith(f".{args.source}"):
                prefix = file_name[0:-(len(args.source)+1)]
                target_file = f"{prefix}.{args.target}"
                s_file = os.path.abspath(os.path.join(args.dir, subfolder, file_name))
                t_file = os.path.abspath(os.path.join(args.dir, subfolder, target_file))

                with open(s_file) as sfh, open(t_file) as tfh:
                    filenames[target_file] = (stripread(sfh), stripread(tfh))

    jsondata = json.load(open(args.json_file))
    print(f"src-trg sentence pairs = {len(jsondata)}", file=sys.stderr)

    for sentence in jsondata:
        filename = sentence["document id"]

        if not filename in filenames:
            print("Fatal: missing file: {filename}", file=sys.stderr)

        ref_prn = sentence["ref pronoun"].lower()

        lineno = int(sentence["segment id"])
        source = filenames[filename][0][lineno-1].strip("\r\n")
        target = filenames[filename][1][lineno-1].strip("\r\n")

        if source and noWS(source) != noWS(sentence["src segment"]):
            print(f"Fatal: bad source", file=sys.stderr)
            sys.exit(1)

        def is_too_long(context):
            if spm:
                return sum([len(x) for x in spm.encode(context + [source])]) > args.max_length
            else:
                return sum([len(x.split()) for x in context + [source]]) > args.max_length

        source_context, target_context = get_context(is_too_long, lineno, filenames[filename])
        source_line = args.separator.join(source_context + [source])
        target_line = args.separator.join(target_context + [target])
        print(source_line, target_line, sep="\t")

        for error in sentence["errors"]:
            contrastive = error["contrastive"]
            target_line = args.separator.join(target_context + [contrastive])
            print(source_line, target_line, sep="\t")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--source", default="en")
    parser.add_argument("-t", "--target", default="de")
    parser.add_argument("-d", "--dir", default="documents")
    parser.add_argument("-m", "--max-length", type=int, default=250)
    parser.add_argument("--separator", default=" <eos> ")
    parser.add_argument("--spm")
    parser.add_argument("json_file")
    args = parser.parse_args()

    main(args)

