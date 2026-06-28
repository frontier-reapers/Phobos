# Phobos
Phobos is script for dumping EVE client data into JSON format.

It uses collection of data miners which extract data from files of various formats. It does not provide stable "API" by design: if CCP changes data scheme within EVE client, output files will also change.

### A note on safety
Several data miners used in Phobos are doing potentially very dangerous thing security-wise, they are loading external code:
 
- ResourcePickleMiner: [unpickles](https://docs.python.org/2.7/library/pickle.html) serialized python files
- FsdBinaryMiner: executes loaders provided by the EVE client to access data in FSD binary format
 
It doesn't mean that you should not use these miners. Generally speaking, if you trust EVE client and Phobos - you should have no issues with these miners. Phobos runs simple validation on files which will be worked upon (checksum according to the client's file registry). Still, it is recommended to run Phobos in some sandboxed environment (e.g. separate Wine prefix for Linux).

### Requirements

* Python 3.12
* 64-bit python built for Windows is needed to access data in FSD binary format

### Unified Build Pipeline

To run the full extraction and generation pipeline in one step, use the unified build command:

    $ python -m scripts.build_all --eve="C:\CCP\EVE Frontier" --output ./out

This will extract raw data into `./out/raw/` and then run all downstream generators (universe database, ship CSV, item icons, and landscapes) into `./out`.

### Arguments:
* `--eve`: Required. Path to EVE client folder, e.g. `C:\CCP\EVE Online`.
* `--output` or `-o`: Required. Output directory for all generated artifacts.
* `--server`: Optional. Server to pull data from. Defaults to `stillness`.
* `--translate`: Optional. Specifies language to which strings will be translated (default: `multi`).
* `--list`: Optional. Comma-separated list of container names to extract.

### Upstream Extraction Only

If you only need the raw JSON extraction (without downstream generators), you can still run the upstream miner directly:

    $ python run.py --eve=E:\eve\client\ --json=~\Desktop\phobos_tq_en-us --list="evetypes, marketgroups, metadata"

Arguments for `run.py`:

* `--eve`: Required. Path to EVE client folder.
* `--json`: Required. Output folder for JSON files.
* `--server`: Optional. Server to pull data from. Defaults to `stillness`.
* `--translate`: Optional. Language translation mode (default: `multi`).
* `--list`: Optional. Comma-separated container names to extract.

## EVE Universe Database Generator

The `generate.py` script extracts EVE universe data from Phobos output and creates a normalized SQLite database with systems, constellations, regions, and jump connections. This is particularly useful for creating navigation tools, route planners, and universe analysis applications for EVE Frontier.

### Requirements for generate.py

* Phobos output files (run the main extraction first)
* Python 3.7+ (no additional dependencies required)

### Usage

First, run Phobos to extract the raw EVE client data:

    $ python -m run --eve="C:\CCP\EVE Frontier" --json=output --translate=multi

Then use the generated output to create the universe database:

    $ python -m scripts.generate --output eve_universe.db --phobos-output ./output

> **Note:** The `python -m scripts.<name>` invocation pattern is the supported way to run relocated generators. It ensures the project root is on `sys.path`, allowing clean absolute imports. You can also use the unified build pipeline instead: `python -m scripts.build_all ...`

### Arguments for generate.py

* `--output` or `-o`: Optional. Output SQLite database path (default: `eve_universe.db`)
* `--phobos-output` or `-p`: Optional. Path to Phobos output directory (default: `./output`)
* `--query` or `-q`: Optional. Run a simple query on the database after creation

### Examples

Create a database with default settings:

    $ python -m scripts.generate

Create a database with custom paths:

    $ python -m scripts.generate --output frontier_universe.db --phobos-output ./phobos_data

Create database and run a query:

    $ python -m scripts.generate --query "SELECT COUNT(*) FROM SolarSystems"

### Database Schema

The generated SQLite database contains the following tables:

* **Regions**: Region data with coordinates
* **Constellations**: Constellation data with region links  
* **SolarSystems**: Solar systems with coordinates, star data, constellation/region links
* **Jumps**: Stargate connections between systems (bidirectional)
* **Planets**: Planet data with celestial information and proper naming
* **Moons**: Moon data orbiting planets with proper naming
* **NpcStations**: NPC-owned stations in space

## Ship Data CSV Export

The `generate_ship_csv.py` script extracts detailed ship attributes from EVE Frontier client files and exports them to CSV format for analysis in Excel, Python, databases, or other tools.

### Usage

**Option 1: Generate from existing Phobos output**

If you've already run the main extraction:

    $ python -m scripts.generate_ship_csv

This creates `ship_data.csv` with all ship attributes.

**Option 2: Extract and generate in one step**

    $ python -m scripts.generate_ship_csv --eve "C:\CCP\EVE Frontier"

This will automatically run the data extraction first if needed, then generate the CSV.

**Custom output location:**

    $ python -m scripts.generate_ship_csv --output my_ships.csv

### CSV Output

The generated CSV contains 20 attributes for each ship:

- **Identity**: Faction, Ship Name, Class (Shuttle, Corvette, Frigate, etc.)
- **Structure**: HP, Mass, Volume (packaged/unpacked), Cargo Capacity
- **Performance**: Max Velocity, Warp Speed, Inertia Modifier
- **Defense**: Shield Recharge Time, Capacitor, Heat Capacity
- **Targeting**: Max Range, Max Targets, Signature Radius, Scan Resolution
- **Resources**: Fuel Capacity

**Example output:**
```
Faction,ShipName,Class,StructureHP,Capacity_m3,FuelCapacity_units,Mass_kg,...
Keep,Wend,Shuttle,750.0,520.0,200.0,6800000.0,...
Exclave,USV,Frigate,2160.0,3120.0,2420.0,30266600.0,...
Synod,Carom,Corvette,1300.0,300.0,3000.0,7200000.0,...
```

### Requirements

Requires extracted JSON data from Phobos. If not already extracted, run:

    $ python -m run --eve "C:\CCP\EVE Frontier" --json output --translate=multi

For detailed documentation, troubleshooting, and integration examples, see [SHIP_DATA_EXPORT.md](docs/SHIP_DATA_EXPORT.md).

---

## Other Tools

### Image Extractor
`scripts/generate_image_zip.py` extracts item icons from the EVE client resource files and packages them into a ZIP archive.
See [SCRIPTS_REFERENCE.md](docs/SCRIPTS_REFERENCE.md#generate_image_zippy) for usage.

### Output Cleaner
`tools/tidy_outputs.py` reduces the size of Phobos JSON output by removing redundant or constant keys.
See [SCRIPTS_REFERENCE.md](docs/SCRIPTS_REFERENCE.md#toolstidy_outputspy) for usage.

### Diagnostic Tools
`tools/compare_db_schema.py` is a developer utility for comparing database schemas.
See [SCRIPTS_REFERENCE.md](docs/SCRIPTS_REFERENCE.md) for usage.

### Running Scripts Standalone

All relocated generators support standalone invocation via `python -m scripts.<name>`. This ensures the project root is on `sys.path`, allowing clean absolute imports (e.g., `import run`, `from util.resource_browser import ...`). For example:

    $ python -m scripts.generate --output my.db --phobos-output ./raw
    $ python -m scripts.generate_image_zip --eve "C:\CCP\EVE Frontier" --verbose
    $ python -m scripts.extract_landscapes
    $ python -m scripts.query_blueprints --search "gyrojet"

> **Tip:** If you previously used `python generate.py` or `python generate_ship_csv.py`, switch to the `python -m scripts.<name>` pattern after the reorganization.

### Sample Queries

Show systems with their jump connections:
```sql
SELECT s.name, COUNT(j.toSystemId) as connections 
FROM SolarSystems s 
LEFT JOIN Jumps j ON s.solarSystemId = j.fromSystemId 
GROUP BY s.solarSystemId 
ORDER BY connections DESC 
LIMIT 10;
```

Find route between systems (basic):
```sql
WITH RECURSIVE route(system_id, path, hops) AS (
  SELECT 30000001, '30000001', 0
  UNION
  SELECT j.toSystemId, path || '->' || j.toSystemId, hops + 1
  FROM route r, Jumps j 
  WHERE r.system_id = j.fromSystemId AND hops < 5 AND j.toSystemId = 30000002
)
SELECT * FROM route WHERE system_id = 30000002;
```

Show planets in a system with proper naming:
```sql
SELECT name, celestialIndex, radius, orbitRadius 
FROM Planets 
WHERE solarSystemId = 30005266
ORDER BY celestialIndex;
```

Find all moons of a specific planet:
```sql
SELECT m.name, m.celestialIndex, m.radius, m.orbitRadius
FROM Moons m
JOIN Planets p ON m.planetId = p.planetId
WHERE p.name = 'U87-QF1 - Planet 4'
ORDER BY m.celestialIndex;
```

### Performance

The script processes approximately:
- 24,400+ systems from EVE Frontier universe data
- 7,400+ stargate connections
- 83,300+ planets with proper naming
- 152,500+ moons with hierarchical naming 
- 50+ NPC stations 
- Complete extraction typically takes 10-30 seconds

### Phobos-specific data
Besides raw data Phobos pulls from client, it provides two custom containers.

#### phobos/metadata
Contains just two parameters: client version and UNIX timestamp of the time script was invoked.

#### phobos/traits
Traits for various ships. Data has following format:

    Returned value:
      For single language: ({'typeID': int, 'traits': traits}, ...)
      For multi-language: ({'typeID': int, 'traits_en-us': traits, 'traits_ru': traits, ...}, ...)
      Traits: {'skills': (skill section, ...), 'role': role section, 'misc': misc section}
        // skills, role and misc fields are optional
      Section: {'header': string, 'bonuses': (bonus, ...)}
      Bonus: {'number': string, 'text': string}
        // number field is optional

For example, Cambion traits in JSON format:

    {
      "traits": {
        "role": {
          "bonuses": [
            {"number": "115%", "text": "bonus to kinetic Light Missile and Rocket damage"},
            {"number": "50%", "text": "reduction in module heat damage amount taken"},
            {"text": "·Can fit Assault Damage Controls"}
          ],
          "header": "Role Bonus:"
        }, 
        "skills": [
          {
            "bonuses": [{"number": "5%", "text": "bonus to Light Missile and Rocket Launcher rate of fire"}],
            "header": "Assault Frigates bonuses (per skill level):"
          },
          {
            "bonuses": [{"number": "4%", "text": "bonus to all shield resistances"}],
            "header": "Caldari Frigate bonuses (per skill level):"
          }
        ]
      },
      "typeID": 32788
    },
