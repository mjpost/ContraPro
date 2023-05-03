#!/usr/bin/env python3

import os
import re
import sys
import json


def noWS(s):
    """Removes all whitespace for an easy comparison"""
    return re.sub(r'[\s\t\n"`´\']', "", s)


def build_doc(is_too_long, count_tokens, lineno, doc, tokens_before=None, num_before=None):
    """Create the document instance from previous and future sentences.
    If num_before is not None, use only num_before lines as preceding context (the rest as future).

    :param is_too_long: The function to call to see if the line is too long
    :param count_tokens: Inelegant second function that counts tokens
    :param lineno: The line number (zero-indexed)
    :param doc: the document
    :param num_before: The number of context sentences to put before (None=infinite)
    :return:
    """
    context_line = lineno - 1

    source_doc = [doc[0][lineno]]
    target_doc = [doc[1][lineno]]

    # Add previous context, up to space (is_too_long) and permission (num_before)
    added_tokens = 0
    while context_line >= 0 and (num_before is None or num_before > 0):
        if tokens_before is not None:
            # Don't add the line if it won't fit
            added_tokens += count_tokens(doc[0][context_line])
            if added_tokens > tokens_before:
                break

        source_doc.insert(0, doc[0][context_line])
        target_doc.insert(0, doc[1][context_line])
        if is_too_long(source_doc):
            source_doc.pop(0)
            target_doc.pop(0)
            break

        context_line -= 1

        if num_before is not None:
            num_before -= 1

    index = len(source_doc) - 1

    # If permitted, add future context, up to space
    if num_before is not None:
        context_line = lineno + 1
        while context_line < len(doc[0]):
            source_doc.append(doc[0][context_line])
            target_doc.append(doc[1][context_line])
            if is_too_long(source_doc):
                source_doc.pop()
                target_doc.pop()
                break

            context_line += 1

    return source_doc, target_doc, index


def stripread(fh):
    lines = []
    for line in fh:
        lines.append(line.rstrip("\r\n"))
    return lines


def read_dir_recursive(dir, source, target, remove_ext=False):
    filenames = {}

    for subfolder in os.listdir(dir):
        if os.path.isdir(os.path.join(dir, subfolder)):
            for file_name in os.listdir(os.path.join(dir, subfolder)):
                if file_name.endswith(f".{source}"):
                    prefix = file_name[0:-(len(source)+1)]
                    source_file_path = os.path.abspath(os.path.join(dir, subfolder, file_name))
                    target_file = f"{prefix}.{target}"
                    target_file_path = os.path.abspath(os.path.join(dir, subfolder, target_file))

                    key = prefix if remove_ext else target_file
                    with open(source_file_path) as sfh, open(target_file_path) as tfh:
                        filenames[key] = (stripread(sfh), stripread(tfh))

    return filenames


def main(args):
    spm = None
    if args.spm:
        from sentencepiece import SentencePieceProcessor
        spm = SentencePieceProcessor(model_file=args.spm)

    filenames = read_dir_recursive(args.dir, args.source, args.target)

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

        # used to create a parallel corpus with non-pronoun events
        lineno += args.offset

        # skip if the line number can't be found
        if len(filenames[filename][0]) <= lineno:
            continue

        source = filenames[filename][0][lineno].strip("\r\n")
        target = filenames[filename][1][lineno].strip("\r\n")

        def count_tokens(line):
            if type(line) == str:
                line = [line]

            if spm:
                return len(spm.encode(args.separator.join(line)))
                # print(length, spm.encode(args.separator.join(context + [source])))
            else:
                return len(args.separator.join(line).split())
                # print(length, args.separator.join(context + [source]).split())

        def is_too_long(source_doc):
            """Return True if the context + source sentence is too long."""
            length = count_tokens(source_doc)
            return (args.max_tokens is not None and length > args.max_tokens) or (args.max_sents is not None and len(source_doc) - 1 > args.max_sents)

        if not args.offset and source and noWS(source) != noWS(sentence["src segment"]):
            print(f"Warning: bad source in", filename, "line", lineno, file=sys.stderr)
            print("-> file: ", noWS(source), file=sys.stderr)
            print("-> json: ", noWS(sentence["src segment"]), file=sys.stderr)

        source_lines, target_lines, target_index = build_doc(is_too_long, count_tokens, lineno, filenames[filename], num_before=args.sents_before, tokens_before=args.tokens_before)

        # {'ante distance': 0, 'ref pronoun': 'es', 'src pronoun': 'it', 'corpus': 'opensubs1921-ende', 'document id': '1921_12806_3712161.de', 'errors': [{'contrastive': 'Jetzt hast du mich mit deiner Erzählung aber neugierig gemacht, und ich bin gespannt zu hören, wie sie weiterging!', 'replacement': 'sie', 'replacement gender': 'Fem', 'type': 'pronominal coreference'}, {'contrastive': 'Jetzt hast du mich mit deiner Erzählung aber neugierig gemacht, und ich bin gespannt zu hören, wie er weiterging!', 'replacement': 'er', 'replacement gender': 'Masc', 'type': 'pronominal coreference'}], 'intrasegmental': True, 'ref ante head': None, 'ref ante head gender': None, 'ref ante head id': None, 'ref ante head lemma': None, 'ref ante head morpho': None, 'ref ante head pos': None, 'ref ante phrase': None, 'ref segment': 'Jetzt hast du mich mit deiner Erzählung aber neugierig gemacht, und ich bin gespannt zu hören, wie es weiterging!', 'segment id': 70, 'src ante head': 'story', 'src ante head gender': None, 'src ante head id': 9, 'src ante head lemma': 'story', 'src ante head morpho': None, 'src ante head pos': 'NN', 'src ante phrase': 'your story', 'src segment': "You have made me very curious about your story and I can't wait to hear how it continues!"}
        distance = sentence["ante distance"]

        source_line = args.separator.join(source_lines)
        target_line = args.separator.join(target_lines)

        print(target_index, distance, "correct", ref_prn, source_line, target_line, sep="\t")
        if not args.correct_only:
            for error in sentence["errors"]:
                target_lines[target_index] = error["contrastive"]
                target_line = args.separator.join(target_lines)
                print(target_index, distance, "contrastive", error["replacement"], source_line, target_line, sep="\t")


if __name__ == "__main__":
    BASEDIR = os.path.join(os.path.dirname(__file__), "..")

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", "-s", default="en")
    parser.add_argument("--target", "-t", default="de")
    parser.add_argument("--dir", "-d", default=os.path.join(BASEDIR, "documents"))
    parser.add_argument("--max-sents", "-ms", type=int, default=None, help="Maximum number of context sentences")
    parser.add_argument("--max-tokens", "-m", type=int, default=None, help="Maximum length in subword tokens")
    parser.add_argument("--sents-before", "-sb", type=int, default=None, help="Num sentences previous context")
    parser.add_argument("--tokens-before", "-tb", type=int, default=None, help="Num tokens in previous context")
    parser.add_argument("--separator", default=" <eos>")
    parser.add_argument("--spm")
    parser.add_argument("--zero", "-0", action="store_true", help="indices are already zeroed (French)")
    parser.add_argument("--offset", type=int, default=0, help="Add this number to each segment ID")
    parser.add_argument("--correct-only", action="store_true", help="only output correct lines")
    parser.add_argument("--json-file", "-j", default=os.path.join(BASEDIR, "contrapro.json"))
    args = parser.parse_args()

    main(args)

