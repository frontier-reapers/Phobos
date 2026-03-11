# Ship Data CSV Export

## Overview

The `generate_ship_csv.py` script extracts ship data from EVE Frontier/Online client files and exports it to a CSV file with detailed ship attributes.

## Quick Start

```bash
# Generate ship_data.csv from already-extracted data
python generate_ship_csv.py

# Extract data and generate CSV in one step
python generate_ship_csv.py --eve "C:\CCP\EVE Online"

# Custom output filename
python generate_ship_csv.py --output my_ships.csv
```

## CSV Output Format

The generated CSV contains the following columns:

| Column | Unit | Description |
|--------|------|-------------|
| `Faction` | - | Ship faction (Keep, Synod, Exclave, etc.) |
| `ShipName` | - | Ship name |
| `Class` | - | Ship class (Shuttle, Corvette, Frigate, Destroyer, Cruiser, etc.) |
| `StructureHP` | HP | Structure hit points |
| `Capacity_m3` | m³ | Cargo capacity |
| `FuelCapacity_units` | units | Fuel tank capacity |
| `Mass_kg` | kg | Ship mass |
| `VolumeUnpackaged_m3` | m³ | Volume when assembled |
| `VolumePackaged_m3` | m³ | Volume when packaged |
| `InertiaModifier` | - | Inertia modifier (affects acceleration) |
| `ShieldRecharge_s` | seconds | Shield recharge time |
| `Capacitor_GJ` | GJ | Capacitor capacity |
| `SpecificHeat_C` | C | Specific heat capacity (overheating) |
| `Conductance_k` | k | Heat conductance |
| `MaxTargetRange_km` | km | Maximum targeting range |
| `MaxLockedTargets` | - | Maximum number of targets that can be locked |
| `SignatureRadius_m` | m | Signature radius (scan difficulty) |
| `ScanResolution_mm` | mm | Scan resolution (targeting speed) |
| `MaxVelocity_mps` | m/s | Maximum velocity |
| `WarpSpeed_c` | c | Warp speed multiplier |

## Prerequisites

The script requires extracted JSON data from the EVE client. If you haven't extracted data yet:

```bash
# Extract all data with multi-language support
python run.py --eve "C:\CCP\EVE Online" --json output --translate=multi

# Or extract only required containers (faster)
python run.py --eve "C:\CCP\EVE Online" --json output --translate=multi \
    --list="types,groups,categories,typedogma,factions"
```

## Command Line Options

```
python generate_ship_csv.py [OPTIONS]

Options:
  --output, -o FILE       Output CSV filename (default: ship_data.csv)
  --data-dir, -d DIR      Directory with extracted JSON (default: output)
  --eve PATH             EVE client path (runs extraction if needed)
  --help, -h             Show help message
```

## Examples

### Basic Usage

Generate CSV from default `output/` directory:

```bash
python generate_ship_csv.py
```

Output:
```
Loading data files...
Loaded 45823 types, 1247 groups, 43 categories

Found 342 ships

✓ Ship data written to: ship_data.csv
  Total ships: 342

Sample ships:
  - Exclave: USV (Frigate)
  - Exclave: Lorha (Frigate)
  - Exclave: MCF (Frigate)
  - Exclave: Tades (Destroyer)
  - Exclave: HAF (Frigate)
```

### Custom Output Location

```bash
python generate_ship_csv.py --output exports/eve_ships_2026.csv
```

### Extract and Export in One Command

```bash
python generate_ship_csv.py --eve "C:\Games\EVE Online" --output my_ships.csv
```

### Use Custom Data Directory

If you extracted data to a non-standard location:

```bash
python generate_ship_csv.py --data-dir custom_output --output ships.csv
```

## Ship Classification

The script automatically classifies ships into categories:

### Standard Classes
- **Shuttle** - Basic transport
- **Corvette** - Starter ships
- **Frigate** - Fast, light combat ships
- **Destroyer** - Anti-frigate ships
- **Cruiser** - Medium combat ships
- **Battlecruiser** - Heavy cruisers
- **Battleship** - Large combat ships
- **Capital** - Capital ships (carriers, dreadnoughts, etc.)

### EVE Frontier Classes
- **USV** - Utility Support Vessel
- **MCF** - Multi-role Combat Frigate
- **HAF** - Heavy Assault Frigate
- **Lorha** - Frontier frigate variant
- **Tades** - Frontier destroyer
- **Maul** - Frontier cruiser
- **Combat Battlecruiser** - Frontier battlecruiser

### Specialized Classes
- **Logistics** - Support/repair ships
- **Mining Barge** - Mining ships
- **Exhumer** - Advanced mining ships
- **Freighter** - Large cargo ships
- **Industrial** - Cargo ships
- **Command Ship** - Fleet command ships

## Faction Detection

Ships are assigned to factions based on:

1. **Explicit faction ID** from type data
2. **Type name parsing** for Frontier factions (Keep, Synod, Exclave)
3. **Meta group analysis** for tech variants

Unknown factions are labeled as "Unknown".

## Data Filtering

The script automatically filters:

- ✓ **Includes**: Published, flyable ships with valid attributes
- ✗ **Excludes**: 
  - Unpublished test ships
  - Structures and deployables
  - Ships with incomplete data
  - Non-player entities

## Attribute Mapping

The script uses CCP's dogma attribute IDs to extract ship properties:

```python
ATTRIBUTE_MAP = {
    'hp': 9,                    # Structure HP
    'capacity': 38,             # Cargo capacity
    'fuelCapacity': 1764,       # Fuel capacity
    'mass': 4,                  # Mass
    'volume': 161,              # Volume unpacked
    'volumePackaged': 1313,     # Volume packaged
    'inertiaModifier': 70,      # Inertia
    # ... (see script for complete list)
}
```

These IDs are stable across EVE versions.

## Troubleshooting

### "Data directory not found"

**Solution**: Extract data first:
```bash
python run.py --eve "C:\CCP\EVE Online" --json output --translate=multi
```

### "Required file not found: types.json"

**Solution**: Ensure complete extraction with required containers:
```bash
python run.py --eve "C:\CCP\EVE Online" --json output --translate=multi \
    --list="types,groups,categories,typedogma,factions"
```

### "No ships found in data"

**Possible causes**:
- Incomplete extraction
- Client version incompatibility
- Data corruption

**Solution**: Re-run extraction with verbose output:
```bash
python run.py --eve "C:\CCP\EVE Online" --json output --translate=multi --verbose
```

### Large File Size Warning

If `types.json` is very large (>50MB):
- Normal for complete EVE data
- Script handles large files efficiently
- Consider filtering extraction to specific containers if memory is limited

## Integration Examples

### Python Analysis

```python
import pandas as pd

# Load ship data
ships = pd.read_csv('ship_data.csv')

# Analyze by class
print(ships.groupby('Class')['StructureHP'].mean())

# Find fastest ships
fastest = ships.nlargest(10, 'MaxVelocity_mps')
print(fastest[['ShipName', 'Class', 'MaxVelocity_mps']])

# Compare factions
faction_stats = ships.groupby('Faction').agg({
    'StructureHP': 'mean',
    'MaxVelocity_mps': 'mean',
    'Capacity_m3': 'mean'
})
print(faction_stats)
```

### Excel/Google Sheets

1. Open CSV in Excel/Sheets
2. Use pivot tables to analyze by Class/Faction
3. Create charts for ship comparisons
4. Filter and sort by any attribute

### SQL Database Import

```sql
CREATE TABLE ships (
    Faction TEXT,
    ShipName TEXT,
    Class TEXT,
    StructureHP REAL,
    Capacity_m3 REAL,
    -- ... (other columns)
);

.mode csv
.import ship_data.csv ships
```

## Performance Notes

- **Extraction time**: 5-15 minutes (full data)
- **CSV generation**: 5-30 seconds
- **Output size**: ~50-200 KB (depending on ship count)
- **Memory usage**: ~500 MB (for large types.json)

## Version Compatibility

- **Python**: 3.12+ required
- **EVE Online**: All recent versions
- **EVE Frontier**: Fully supported
- **Platform**: Cross-platform (Windows, Linux, macOS)

## Related Scripts

- [run.py](SCRIPTS_REFERENCE.md#runpy) - Extract client data
- [generate.py](SCRIPTS_REFERENCE.md#generatepy) - Generate universe database
- [query_blueprints.py](SCRIPTS_REFERENCE.md#query_blueprintspy) - Query manufacturing data

## See Also

- [DATA_CONTAINERS.md](DATA_CONTAINERS.md) - Available data containers
- [SCRIPTS_REFERENCE.md](SCRIPTS_REFERENCE.md) - All script documentation
- [DATABASE_GENERATION.md](DATABASE_GENERATION.md) - Universe database guide
