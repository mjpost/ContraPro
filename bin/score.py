#!/usr/bin/env python3

import sys

correct = 0
for lineno, line in enumerate(sys.stdin, 1):
    pronoun, doc = line.rstrip().split("\t")

    last_sentence_tokens = doc.split(" <eos> ")[-1].lower().split()

    if pronoun.lower() in last_sentence_tokens:
        correct += 1

print(correct, lineno, f"{100 * correct / lineno:.1f}%")
