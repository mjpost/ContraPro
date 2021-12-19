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


def get_context(length, lineno, doc):
    context_line = lineno - 1

    source_context = []
    target_context = []
    while context_line >= 1:
        source_context.insert(0, doc[0][context_line-1])
        target_context.insert(0, doc[1][context_line-1])
        context_line -= 1

    return source_context, target_context


def main(args):
    filenames = {}
    for subfolder in os.listdir(args.dir):
        for file_name in os.listdir(os.path.join(args.dir, subfolder)):
            if file_name.endswith(f".{args.source}"):
                prefix = file_name[0:-(len(args.source)+1)]
                target_file = f"{prefix}.{args.target}"
                s_file = os.path.abspath(os.path.join(args.dir, subfolder, file_name))
                t_file = os.path.abspath(os.path.join(args.dir, subfolder, target_file))

                with open(s_file) as sfh, open(t_file) as tfh:
                    filenames[target_file] = (sfh.readlines(), tfh.readlines())

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

        source_context, target_context = get_context(args.max_length, lineno, filenames[filename])
        source_line = args.separator.join(source_context + [source])
        target_line = args.separator.join(target_context + [target])
        print(source_line, target_line, sep="\t")

        # for error in sentence["errors"]:
        #     contrastive = error["contrastive"]
        #     print(context + [contrastive], sep=args.separator)

# sub printContext{
#     my $context = $_[0];
#     my $line = $_[1];
#     my $filename = $_[2];
#     my $filenames = $_[3];
#     my $json_out_s = $_[4];
#     my $json_out_t = $_[5];

#     my %json_context_s =();
#     my %json_context_t =();
#     my $i=1;

#     for(my $c=$context;$c>=1;$c--){
#         my $src_line ="\n";
#         my $trg_line = "\n";
#         if($line-$c >= 1){
#                 $src_line = @{$filenames->{$filename}{"src"}}[$line-$c];
#                 $trg_line = @{$filenames->{$filename}{"trg"}}[$line-$c]; 
#         }
#         if($context_json){
#                 $src_line =~ s/\n//;
#                 $trg_line =~ s/\n//;
#                 $json_context_s{$i} = $src_line;
#                 $json_context_t{$i} = $trg_line;
#                 $i++;
#         }
#         else{
#                 print OUT_S_CONTEXT $src_line;
#                 print OUT_T_CONTEXT $trg_line;
#        }
#         if($context_json){
#                 push(@{$json_out_s}, \%json_context_s );
#                 push(@{$json_out_t}, \%json_context_t );
#         }
#     }

# }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--source", default="en")
    parser.add_argument("-t", "--target", default="de")
    parser.add_argument("-d", "--dir", default="documents")
    parser.add_argument("-m", "--max-length", type=int, default=250)
    parser.add_argument("--separator", default=" <eos> ")
    parser.add_argument("json_file")
    args = parser.parse_args()

    main(args)

