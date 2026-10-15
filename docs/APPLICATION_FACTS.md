# What you can truthfully say in the application (as of this build)

The challenge asks applicants to disclose development stage, prototype status and testing/pilot evidence.
Use these as your factual baseline and update them as things change.

## Development stage / prototype status
- Working web prototype: citizen portal + authority portal, PostgreSQL/PostGIS database, REST API, React UI.
- Implemented and tested: authentication with roles, issue reporting with image upload and location,
  priority scoring, duplicate detection (distance + category + time), department routing, authority dashboard,
  hotspot map, assignment/resolution/verification workflow with before/after photos.
- Automated tests: see `docs/TEST_REPORT.md` (regenerate it on your own machine and quote that number).

## AI — claim only what you have measured
- Road-damage detection: YOLO model trained on public RDD2022 imagery (India subset) — *only after you train it*.
  Quote precision/recall/mAP from `evaluation_results.json`, measured on your held-out split, and say the split is
  your own (the public test labels are not available).
- Say "model confidence", never "accuracy".
- Garbage, water leakage and streetlight: no custom model unless you build one. Say they are selected by the citizen
  (or classified by a pretrained model only if you actually test one).
- Do NOT say the model is trained on Maharashtra data unless you collected and used it.

## Data
- Demo data is synthetic (labelled in the UI). No real citizen data was used.
- State the source and licence of every validation image (`data/validation/sources.csv`).

## Methodology disclosures
- Priority = 0.30 Severity + 0.20 Frequency + 0.20 Location + 0.15 Traffic + 0.15 Time — your prototype rule, not an official
  policy. Traffic is a per-category proxy; location criticality is keyword-based.
- Correction to the original blueprint: its worked example (90, 80, 90, 75, 60) gives **81.25**, not 81.75.
- Duplicate detection: same category within 25 m merges; 25–60 m is flagged for human review. No image similarity.
- Resolution verification is human-confirmed.

## Do NOT claim
Pilots or deployments, users or beneficiaries you don't have, government/municipal partnerships or integrations,
production readiness or scale, accuracy figures you didn't measure, real-time traffic data, blockchain/IoT/drone features.

## Honest "next steps"
Pilot with a ward office, more categories, mobile app, Marathi voice input, image-based resolution verification,
object storage and production hardening.
