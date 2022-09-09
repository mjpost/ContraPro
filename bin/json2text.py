#!/usr/bin/env python

import os
import re
import sys
import json


def noWS(s):
    """Removes all whitespace for an easy comparison"""
    return re.sub(r'[\s\t\n"`´\']', "", s)


def get_context(is_too_long, lineno, doc):
    """Builds the context backwards, calling {is_too_long} to determine when to stop."""

    context_line = lineno - 1

    source_context = []
    target_context = []
    while context_line >= 0:
        source_context.insert(0, doc[0][context_line])
        target_context.insert(0, doc[1][context_line])
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
    # print(f"src-trg sentence pairs = {len(jsondata)}", file=sys.stderr)

    for sentence in jsondata:
        filename = sentence["document id"]
        if not filename.endswith(f".{args.target}"):
            filename += "." + args.target

        if not filename in filenames:
            print("Fatal: missing file: {filename}", file=sys.stderr)

        ref_prn = sentence["ref pronoun"].lower()

        lineno = int(sentence["segment id"])
        if not args.zero:
            lineno -= 1
        source = filenames[filename][0][lineno].strip("\r\n")
        target = filenames[filename][1][lineno].strip("\r\n")

        def is_too_long(context):
            """Determine if the context is too long. Remember to count the <eos> tokens."""
            length = 0
            if spm:
                length = len(spm.encode(args.separator.join(context + [source])))
            else:
                length = len(args.separator.join(context + [source]).split())

            return length > args.max_tokens or (args.max_sents > 0 and len(context) > args.max_sents)

        if source and noWS(source) != noWS(sentence["src segment"]):
            print(f"Warning: bad source in", filename, "line", lineno, file=sys.stderr)
            print("-> file: ", noWS(source), file=sys.stderr)
            print("-> json: ", noWS(sentence["src segment"]), file=sys.stderr)

        source_context, target_context = get_context(is_too_long, lineno, filenames[filename])
        source_line = args.separator.join(source_context + [source])
        target_line = args.separator.join(target_context + [target])

        # {'ante distance': 0, 'ref pronoun': 'es', 'src pronoun': 'it', 'corpus': 'opensubs1921-ende', 'document id': '1921_12806_3712161.de', 'errors': [{'contrastive': 'Jetzt hast du mich mit deiner Erzählung aber neugierig gemacht, und ich bin gespannt zu hören, wie sie weiterging!', 'replacement': 'sie', 'replacement gender': 'Fem', 'type': 'pronominal coreference'}, {'contrastive': 'Jetzt hast du mich mit deiner Erzählung aber neugierig gemacht, und ich bin gespannt zu hören, wie er weiterging!', 'replacement': 'er', 'replacement gender': 'Masc', 'type': 'pronominal coreference'}], 'intrasegmental': True, 'ref ante head': None, 'ref ante head gender': None, 'ref ante head id': None, 'ref ante head lemma': None, 'ref ante head morpho': None, 'ref ante head pos': None, 'ref ante phrase': None, 'ref segment': 'Jetzt hast du mich mit deiner Erzählung aber neugierig gemacht, und ich bin gespannt zu hören, wie es weiterging!', 'segment id': 70, 'src ante head': 'story', 'src ante head gender': None, 'src ante head id': 9, 'src ante head lemma': 'story', 'src ante head morpho': None, 'src ante head pos': 'NN', 'src ante phrase': 'your story', 'src segment': "You have made me very curious about your story and I can't wait to hear how it continues!"}
        distance = sentence["ante distance"]

        print(distance, "correct", ref_prn, source_line, target_line, sep="\t")
        if not args.correct_only:
            for error in sentence["errors"]:
                contrastive = error["contrastive"]
                target_line = args.separator.join(target_context + [contrastive])
                print(distance, "contrastive", error["replacement"], source_line, target_line, sep="\t")


if __name__ == "__main__":
    BASEDIR = os.path.join(os.path.dirname(__file__), "..")

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--source", default="en")
    parser.add_argument("-t", "--target", default="de")
    parser.add_argument("-d", "--dir", default=os.path.join(BASEDIR, "documents"))
    parser.add_argument("--max-sents", "-ms", type=int, default=0, help="Maximum number of context sentences")
    parser.add_argument("--max-tokens", "-m", type=int, default=0, help="Maximum length in subword tokens")
    parser.add_argument("--separator", default=" <eos> ")
    parser.add_argument("--spm")
    parser.add_argument("--zero", "-0", action="store_true", help="indices are already zeroed (French)")
    parser.add_argument("--correct-only", action="store_true", help="only output correct lines")
    parser.add_argument("--json-file", "-j", default=os.path.join(BASEDIR, "contrapro.json"))
    args = parser.parse_args()

    main(args)

