# SevaSetu AI — model

1. Download the India subset of RDD2022 (official repo: github.com/sekilab/RoadDamageDetector).
2. On Colab/Kaggle (GPU): `pip install ultralytics`, then run `training/rdd_pipeline.py prepare`, `train`, `evaluate`.
3. Copy the resulting `best.pt` to `ai/models/sevasetu_road_damage.pt` (the backend loads it automatically;
   override with `MODEL_PATH` in `backend/.env`). Install `ultralytics` in the backend venv too.
4. Keep `evaluation_results.json` — those measured numbers are your application evidence.
