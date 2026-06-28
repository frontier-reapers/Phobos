import json
import csv
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).parent.resolve()
OUT = BASE / "output"
OUT.mkdir(exist_ok=True)

print("Loading ecosystem names...")
with open(BASE / "output" / "fsd_built" / "ecosystem.json", "r") as f:
    ecosystems = json.load(f)
eco_names = {int(k): v["name"] for k, v in ecosystems.items()}

print("Loading landscapes...")
with open(BASE / "output" / "fsd_built" / "landscape.json", "r") as f:
    landscapes = json.load(f)

rows = []
systems = {}

for sys_id, sys_data in landscapes.items():
    entries = []
    for category, items in sys_data.items():
        for item_id, item in items.items():
            tags = ", ".join(item.get("tags", []))
            for site_id, site in item.get("sites", {}).items():
                eco_id = site["ecosystemID"]
                eco_name = eco_names.get(eco_id, f"Unknown({eco_id})")
                entries.append({
                    "category": category,
                    "item_id": int(item_id),
                    "site_id": int(site_id),
                    "ecosystem_id": eco_id,
                    "ecosystem_name": eco_name,
                    "tags": tags,
                })
                rows.append({
                    "solar_system_id": int(sys_id),
                    "category": category,
                    "item_id": int(item_id),
                    "site_id": int(site_id),
                    "ecosystem_id": eco_id,
                    "ecosystem_name": eco_name,
                    "tags": tags,
                })
    systems[int(sys_id)] = entries

print(f"Processed {len(systems)} solar systems, {len(rows)} total site entries.")

# Write per-system JSON
out_json = OUT / "landscapes_per_system.json"
with open(out_json, "w") as f:
    json.dump(systems, f, indent=2)
print(f"Wrote {out_json}")

# Write flattened CSV
out_csv = OUT / "landscapes_per_system.csv"
with open(out_csv, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["solar_system_id", "category", "item_id", "site_id", "ecosystem_id", "ecosystem_name", "tags"])
    writer.writeheader()
    writer.writerows(rows)
print(f"Wrote {out_csv}")

# Write summary: unique landscapes per system (curated)
summary = {}
for sys_id, entries in systems.items():
    names = []
    for e in entries:
        names.append(f"{e['category']}: {e['ecosystem_name']}")
    summary[sys_id] = list(sorted(set(names)))

out_summary = OUT / "landscapes_per_system_summary.json"
with open(out_summary, "w") as f:
    json.dump(summary, f, indent=2)
print(f"Wrote {out_summary}")

print("Done.")
