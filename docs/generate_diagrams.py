"""Builds the architecture / ER / lifecycle diagrams (PNG + SVG) with Graphviz.
    cd backend && python ../docs/generate_diagrams.py        (needs `dot` installed)
The ER diagram is generated from the real SQLAlchemy models, so it always matches the code."""
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.getcwd())
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg2://x:x@localhost/x")
os.environ.setdefault("SECRET_KEY", "diagram")
from app.core.database import Base          # noqa: E402
import app.models                           # noqa: F401,E402

OUT = Path(__file__).resolve().parent / "diagrams"
OUT.mkdir(exist_ok=True)
FONT = 'fontname="DejaVu Sans"'


def render(name, dot):
    (OUT / f"{name}.dot").write_text(dot)
    for fmt in ("png", "svg"):
        extra = ["-Gdpi=170"] if fmt == "png" else []
        subprocess.run(["dot", f"-T{fmt}", *extra, str(OUT / f"{name}.dot"), "-o", str(OUT / f"{name}.{fmt}")], check=True)
    (OUT / f"{name}.dot").unlink()
    print("wrote", name)


# ------------------------------------------------------------------ architecture
render("architecture", f'''digraph G {{
  rankdir=TB; nodesep=0.5; ranksep=0.6; bgcolor="white";
  node [shape=box, style="rounded,filled", {FONT}, fontsize=12, margin="0.2,0.12", color="#3b5bdb", fillcolor="#edf2ff"];
  edge [{FONT}, fontsize=10, color="#555555"];

  citizen [label="Citizen\\nReact web app\\n(report · track)", fillcolor="#e7f5ff", color="#1c7ed6"];
  authority [label="Authority\\nReact web app\\n(dashboard · map · actions)", fillcolor="#f3e8ff", color="#7048e8"];
  api [label="FastAPI backend\\nJWT auth · role checks · REST API", fillcolor="#fff4e6", color="#f08c00"];
  subgraph cluster_services {{
    label="Service layer"; {FONT}; fontsize=12; style="rounded,dashed"; color="#999999";
    ai [label="AI service\\nYOLO road-damage detector\\nclass → category · severity heuristic"];
    prio [label="Priority engine\\n5-factor weighted score"];
    dup [label="Duplicate detection\\nPostGIS distance + category + time window"];
    route [label="Department routing"];
    hot [label="Hotspot detection\\nDBSCAN clustering"];
  }}
  db [label="PostgreSQL + PostGIS\\nusers · civic_issues · issue_reports · assignments\\nresolutions · issue_events · ai_predictions · duplicate_candidates", shape=cylinder, fillcolor="#e6fcf5", color="#0ca678"];
  files [label="Image storage\\n(local uploads/ for the prototype)", shape=folder, fillcolor="#f8f9fa", color="#868e96"];
  model [label="Model weights\\nsevasetu_road_damage.pt\\n(trained offline on RDD2022 data)", shape=note, fillcolor="#fff9db", color="#f59f00"];

  citizen -> api [label="REST / JSON"]; authority -> api [label="REST / JSON"];
  api -> ai; api -> prio; api -> dup; api -> route; api -> hot;
  ai -> model [style=dashed, label="loads"];
  api -> db [label="SQLAlchemy"]; dup -> db [label="ST_DWithin"]; api -> files;
}}''')

# ------------------------------------------------------------------ lifecycle
render("issue_lifecycle", f'''digraph G {{
  rankdir=LR; nodesep=0.35; ranksep=0.45; bgcolor="white";
  node [shape=box, style="rounded,filled", {FONT}, fontsize=12, margin="0.18,0.1"];
  edge [{FONT}, fontsize=10, color="#555555"];
  sub [label="Citizen submits\\nphoto + location + text", fillcolor="#e7f5ff", color="#1c7ed6"];
  ai [label="AI analysis\\ncategory · model confidence\\nseverity", fillcolor="#fff9db", color="#f59f00"];
  dup [label="Duplicate check\\n≤25 m: merge\\n25–60 m: flag for review", fillcolor="#fff9db", color="#f59f00"];
  pr [label="Priority score\\n0–100", fillcolor="#fff9db", color="#f59f00"];
  rt [label="Routed to\\ndepartment", fillcolor="#fff9db", color="#f59f00"];
  node [fillcolor="#f3e8ff", color="#7048e8"];
  R [label="REPORTED"]; A [label="ASSIGNED"]; P [label="IN PROGRESS"]; S [label="RESOLVED\\n(+ after-photo)"]; V [label="VERIFIED"];
  sub -> ai -> dup -> pr -> rt -> R -> A -> P -> S -> V;
  S -> P [label="rejected /\\nreopened", style=dashed, constraint=false];
}}''')

# ------------------------------------------------------------------ priority formula
render("priority_formula", f'''digraph G {{
  rankdir=LR; bgcolor="white"; nodesep=0.25; ranksep=0.8;
  node [shape=box, style="rounded,filled", {FONT}, fontsize=12, margin="0.2,0.12", fillcolor="#edf2ff", color="#3b5bdb"];
  edge [{FONT}, fontsize=11, color="#555555"];
  sev [label="Severity\\n(AI heuristic: damaged-area share + class)"];
  frq [label="Report frequency\\n(merged reports)"];
  loc [label="Location criticality\\n(keywords: hospital, school, junction…)"];
  trf [label="Traffic / footfall\\n(per-category PROXY)"];
  tim [label="Time unresolved\\n(100 at 72 h)"];
  out [label="Priority score 0–100\\nHIGH ≥ 70 · MEDIUM ≥ 40 · LOW < 40", fillcolor="#fff4e6", color="#f08c00"];
  sev -> out [label="30%"]; frq -> out [label="20%"]; loc -> out [label="20%"]; trf -> out [label="15%"]; tim -> out [label="15%"];
}}''')

# ------------------------------------------------------------------ ER diagram (from the models)
rows = []
fk_edges = []
for t in Base.metadata.sorted_tables:
    fks = {fk.parent.name: fk.column.table.name for fk in t.foreign_keys}
    cells = []
    for c in t.columns:
        tag = "PK" if c.primary_key else ("FK" if c.name in fks else "")
        typ = str(c.type).split("(")[0].lower()
        cells.append(f'<TR><TD ALIGN="LEFT">{c.name}</TD><TD ALIGN="LEFT"><FONT COLOR="#868e96">{typ}</FONT></TD>'
                     f'<TD>{"<FONT COLOR=" + chr(34) + "#c92a2a" + chr(34) + "><B>" + tag + "</B></FONT>" if tag else " "}</TD></TR>')
    for col, target in fks.items():
        fk_edges.append((t.name, target))
    rows.append(f'  {t.name} [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="#3b5bdb">'
                f'<TR><TD COLSPAN="3" BGCOLOR="#3b5bdb"><FONT COLOR="white"><B>{t.name}</B></FONT></TD></TR>{"".join(cells)}</TABLE>>];')
edges = "\n".join(f"  {a} -> {b} [arrowhead=crow, arrowtail=none, color=\"#868e96\"];" for a, b in sorted(set(fk_edges)))
render("database_er", f'''digraph G {{
  rankdir=LR; bgcolor="white"; nodesep=0.35; ranksep=1.1; concentrate=true;
  node [shape=plain, {FONT}, fontsize=10];
  edge [{FONT}];
{chr(10).join(rows)}
{edges}
}}''')
