# Application text — DRAFT (edit before pasting into the portal)

Use only what is true on the day you submit. Items in **[brackets]** need your input.
Check each field's character limit on the portal; these are written to be easy to shorten.

**Project title:** SevaSetu AI — AI-powered civic issue detection, prioritisation and resolution platform
**Sector / sub-theme:** Urban Development — sustainable urban growth, land-use and municipal asset management
**Applicant type:** Individual innovator (women category) — **[confirm this matches the portal's eligibility rules]**

## One-line summary
SevaSetu AI turns citizen-reported civic problems into prioritised, location-aware actions for authorities, using AI, geospatial analysis and a tracked resolution workflow.

## Problem
Civic complaints (potholes, garbage, leaking pipes, dead streetlights) typically reach authorities as unsorted, duplicated reports. It is hard to see which problems are most urgent, which reports describe the same defect, where problems cluster, and whether a reported issue was actually fixed. Citizens rarely get visibility after they file. **[Add one or two sourced facts about your locality only if you can cite them.]**

## Solution
A web platform with two sides. Citizens report an issue with a photo and a map location; the system suggests the category, merges nearby duplicate reports, scores urgency with a transparent formula, and routes the issue to the right department. Authorities see a ranked queue, KPIs, a hotspot map and a workflow to assign, resolve (with an after-photo) and verify. Citizens can track every step.

## What is new / different
- A transparent, explainable priority score (severity, report frequency, location criticality, traffic/footfall proxy, time unresolved), with the breakdown visible to users.
- Geospatial duplicate merging (same category within 25 m) with human review for near-duplicates (25–60 m).
- Density-based hotspot detection over open issues.
- End-to-end lifecycle with before/after evidence and an audit timeline.

## Technology
React front end; FastAPI back end; PostgreSQL with PostGIS; YOLO-based road-damage detection trained on public RDD2022 imagery (India subset); Leaflet/OpenStreetMap maps; automated tests with Pytest.

## Development stage and prototype status (be exact)
- Working web prototype with citizen and authority portals, database, API and workflow — implemented and demonstrable.
- Demonstrated on **synthetic demo data** only (clearly labelled). No pilot, no real citizen data, no government integration.
- AI: **[choose one]**
  (a) "Road-damage detector trained on RDD2022 (India subset) and evaluated on our own held-out split: precision **[x]**, recall **[x]**, mAP50 **[x]**" — only with numbers from your `evaluation_results.json`; or
  (b) "Detector integrated into the report flow; training and evaluation pipelines are ready; held-out results are not yet available."
- Garbage, water leakage and streetlight reports use citizen-selected categories (no custom model yet) **[unless you tested a model]**.

## Testing and validation evidence
- **[N]** automated tests passing against a real PostgreSQL/PostGIS database (see the generated test report; regenerate it on your machine and quote that number). Areas: authentication and roles, issue reporting and validation, priority scoring, duplicate detection, authority workflow, hotspots, resolution, error handling and abuse cases.
- Controlled AI validation set: **[describe only if you built it, with source/licence for each image]**.
- No field pilot yet.

## Beneficiaries (intended)
Citizens who report problems (transparent tracking); municipal/ward departments (ranked queue, fewer duplicate tickets, hotspot view); planners (recurring-defect visibility). **No beneficiary counts are claimed.**

## Feasibility and scalability
Uses standard open-source components and runs locally or on a small cloud server. Next: pilot with a ward-level office, locally collected validation images, more categories, mobile and Marathi support, object storage and production hardening.

## Risks and limits (state them)
Model accuracy on local roads is unproven until validated; traffic and location-criticality inputs are proxies; verification is human-confirmed; photo privacy (faces, number plates) must be handled before any real deployment.

## Resources / support requested
Mentorship, a ward-level pilot partner, and help validating the model on local data. **[Adjust to what you actually need.]**
