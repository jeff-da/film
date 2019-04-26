#!/usr/bin/env python3

# Origional file copyright 2017-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import argparse

import json
import os

import h5py
import numpy as np

from string import digits

import vr.programs
from vr.preprocess import tokenize, encode, build_vocab


"""
Preprocessing script for NLVR question files.
"""


parser = argparse.ArgumentParser()
parser.add_argument('--mode', default='prefix',
                    choices=['chain', 'prefix', 'postfix'])
parser.add_argument('--input_questions_json', required=True)
parser.add_argument('--input_vocab_json', default='')
parser.add_argument('--expand_vocab', default=0, type=int)
parser.add_argument('--unk_threshold', default=1, type=int)
parser.add_argument('--encode_unk', default=1, type=int)

parser.add_argument('--output_h5_file', required=True)
parser.add_argument('--output_vocab_json', default='')


def program_to_str(program, mode):
  if mode == 'chain':
    if not vr.programs.is_chain(program):
      return None
    return vr.programs.list_to_str(program)
  elif mode == 'prefix':
    program_prefix = vr.programs.list_to_prefix(program)
    return vr.programs.list_to_str(program_prefix)
  elif mode == 'postfix':
    program_postfix = vr.programs.list_to_postfix(program)
    return vr.programs.list_to_str(program_postfix)
  return None


def main(args):
  if (args.input_vocab_json == '') and (args.output_vocab_json == ''):
    print('Must give one of --input_vocab_json or --output_vocab_json')
    return

  print('Loading data')
  with open(args.input_questions_json, 'r') as f:
    questions = []
    for line in f:
        questions.append(json.loads(line))

  # Either create the vocab or load it from disk
  if args.input_vocab_json == '' or args.expand_vocab == 1:
    print('Building vocab')
    if 'label' in questions[0]:
      answer_token_to_idx = build_vocab(
        (q['label'] for q in questions)
      )
    question_token_to_idx = build_vocab(
      (q['sentence'] for q in questions),
      min_token_count=args.unk_threshold,
      punct_to_keep=[';', ','], punct_to_remove=['?', '.']
    )
    all_program_strs = []
    for q in questions:
      if 'program' not in q: continue
      program_str = program_to_str(q['program'], args.mode)
      if program_str is not None:
        all_program_strs.append(program_str)
    program_token_to_idx = build_vocab(all_program_strs)
    vocab = {
      'question_token_to_idx': question_token_to_idx,
      'program_token_to_idx': program_token_to_idx,
      'answer_token_to_idx': answer_token_to_idx,
    }

  if args.input_vocab_json != '':
    print('Loading vocab')
    if args.expand_vocab == 1:
      new_vocab = vocab
    with open(args.input_vocab_json, 'r') as f:
      vocab = json.load(f)
    if args.expand_vocab == 1:
      num_new_words = 0
      for word in new_vocab['question_token_to_idx']:
        if word not in vocab['question_token_to_idx']:
          print('Found new word %s' % word)
          idx = len(vocab['question_token_to_idx'])
          vocab['question_token_to_idx'][word] = idx
          num_new_words += 1
      print('Found %d new words' % num_new_words)

  if args.output_vocab_json != '':
    with open(args.output_vocab_json, 'w') as f:
      json.dump(vocab, f)

  # Encode all questions and programs
  print('Encoding data')
  questions_encoded = []
  programs_encoded = []
  question_families = []
  orig_idxs = []
  image_idxs = []
  answers = []
  types = []
  for orig_idx, q in enumerate(questions):
    question = q['sentence']

    orig_idxs.append(orig_idx)
    if "LEFT" in q["image_attention"]: # LEFT IMG
        image_idxs.append(int(''.join(c for c in (q['identifier'] + "-img0") if c in digits)))
    else: # RIGHT IMG
        image_idxs.append(int(''.join(c for c in (q['identifier'] + "-img1") if c in digits)))
    question_tokens = tokenize(question,
                        punct_to_keep=[';', ','],
                        punct_to_remove=['?', '.'])
    question_encoded = encode(question_tokens,
                         vocab['question_token_to_idx'],
                         allow_unk=args.encode_unk == 1)
    questions_encoded.append(question_encoded)

    if 'label' in q:
      answers.append(vocab['answer_token_to_idx'][q['label']])

  # Pad encoded questions and programs
  max_question_length = max(len(x) for x in questions_encoded)
  for qe in questions_encoded:
    while len(qe) < max_question_length:
      qe.append(vocab['question_token_to_idx']['<NULL>'])

  # Create h5 file
  print('Writing output')
  questions_encoded = np.asarray(questions_encoded, dtype=np.int32)
  programs_encoded = np.asarray(programs_encoded, dtype=np.int32)
  print(questions_encoded.shape)
  print(programs_encoded.shape)

  mapping = {}
  for i, t in enumerate(set(types)):
    mapping[t] = i

  print(mapping)

  types_coded = []
  for t in types:
    types_coded += [mapping[t]]

  with h5py.File(args.output_h5_file, 'w') as f:
    print(image_idxs)
    f.create_dataset('questions', data=questions_encoded)
    f.create_dataset('image_idxs', data=np.asarray(image_idxs))
    f.create_dataset('orig_idxs', data=np.asarray(orig_idxs))

    if len(programs_encoded) > 0:
      f.create_dataset('programs', data=programs_encoded)
    if len(question_families) > 0:
      f.create_dataset('question_families', data=np.asarray(question_families))
    if len(answers) > 0:
      f.create_dataset('answers', data=np.asarray(answers))
    if len(types) > 0:
      f.create_dataset('types', data=np.asarray(types_coded))


if __name__ == '__main__':
  args = parser.parse_args()
  main(args)
