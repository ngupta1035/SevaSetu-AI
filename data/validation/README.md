# Validation images (controlled test set)

Put labelled test photos in the folders below. These must be images the model was NOT trained on.

| Folder | What goes in it |
|---|---|
| `pothole/` | photos with a pothole / road damage |
| `garbage/` | photos of waste accumulation |
| `leakage/` | photos of water leakage |
| `streetlight/` | photos of damaged/unlit streetlights |
| `negative/` | ordinary road/street photos with NO civic issue (used to measure false positives) |

Record where EVERY image came from in `sources.csv` (own photo / licence + URL / permission). Do not use
images you do not have the right to use, and do not include people's faces or number plates in anything you publish.

Run the evaluation (backend venv, model in place):

    cd backend
    python -m app.evaluation.run_eval --data ../data/validation --out ../docs/ai_eval_app

Aim for at least 20-30 images per class you want to make claims about. Report only what the script prints.
