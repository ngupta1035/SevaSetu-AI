# Demo script (about 5 minutes) — screen recording

## Before you record
- Fresh database → `alembic upgrade head` → `python -m app.seed` → `python -m app.seed_demo`.
- Backend + frontend running; model weights loaded if you have them (otherwise skip the AI chip and say so).
- Internet on (map tiles). Browser at 1280×800, zoom 100%, close other tabs. Two windows: citizen and authority (use a private window).
- Have `backend/uploads/demo/demo_before_pothole.jpg` or a real pothole photo ready to upload.
- Do one dry run; the demo reset is `python -m app.seed_demo --reset`.

## Script
| Time | Screen | Say |
|---|---|---|
| 0:00 | Home page | "Citizens report civic problems, but authorities receive unsorted complaints. SevaSetu AI turns reports into prioritised, location-aware work." |
| 0:20 | Login → *Use citizen demo* → Report Issue | "A citizen uploads a photo and drops a pin." Upload the photo, click the map. |
| 0:50 | After photo selected | If the model is loaded: "The AI suggests the category with its model confidence." If not: "The model isn't loaded in this demo, so the citizen picks the type." Submit. |
| 1:20 | Issue details (priority bars) | "Each issue gets a transparent score: severity, report frequency, location criticality, traffic (a proxy) and time unresolved. This is our prototype rule, not an official policy." |
| 1:50 | Open SS-00001 | "Seven citizens reported the same pothole. The system merged them into one issue because they were within 25 metres — so authorities see one problem with seven reports, ranked higher." |
| 2:20 | Logout → *Use authority demo* → Dashboard | "KPIs, workload by department, and a queue sorted by priority. The banner says this data is synthetic." |
| 3:00 | Map | "Hotspots are clusters of three or more open issues within about 250 metres." Click *Hinjewadi Phase 1* in the ranking to zoom. |
| 3:30 | Issue SS-00001 → Assign → Start work → Mark resolved (after-photo) → Verify | "The authority assigns it, starts work, uploads an after-photo and verifies. Every step is on the timeline." |
| 4:30 | Citizen window → issue page | "The citizen sees the before/after photos and the full history." |
| 4:50 | Slide or README | "Built and tested: [77] automated tests (quote the number from your own fresh run of docs/TEST_REPORT.md). Not yet: a pilot, real users, or a government integration. Next: wider categories, mobile, image-based verification." |

## If something fails live
- Map tiles blank → say "needs internet for OpenStreetMap", continue with the dashboard.
- AI chip missing → the app falls back to manual selection by design.
- Login error → check the backend terminal; `python -m app.seed` recreates the demo accounts.
