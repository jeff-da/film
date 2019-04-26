# python scripts/extract_features.py \
#  --input_image_dir /home/jzda/nlvr2/images/train \
#  --output_h5_file data/train_features.h5

# python scripts/extract_features.py \
#  --input_image_dir /home/jzda/nlvr2/dev \
#  --output_h5_file data/val_features.h5

python scripts/preprocess_questions.py \
  --input_questions_json /home/jzda/code/nlvr/image_attention/single_train_parsed.json \
  --output_h5_file data/train_questions.h5 \
  --output_vocab_json data/vocab.json

python scripts/preprocess_questions.py \
  --input_questions_json /home/jzda/code/nlvr/image_attention/single_dev_parsed.json \
  --output_h5_file data/val_questions.h5 \
  --input_vocab_json data/vocab.json
