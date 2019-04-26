python scripts/extract_features.py \
  --input_image_dir data/CLEVR_v1.0/images/train \
  --output_h5_file data/train_features.h5 \
  --max_images 10

python scripts/extract_features.py \
  --input_image_dir data/CLEVR_v1.0/images/val \
  --output_h5_file data/val_features.h5 \
  --max_images 10

python scripts/preprocess_questions.py \
  --input_questions_json data/CLEVR_v1.0/questions/CLEVR_train_questions.json \
  --output_h5_file data/train_questions.h5 \
  --output_vocab_json data/vocab.json

python scripts/preprocess_questions.py \
  --input_questions_json data/CLEVR_v1.0/questions/CLEVR_val_questions.json \
  --output_h5_file data/val_questions.h5 \
  --input_vocab_json data/vocab.json
