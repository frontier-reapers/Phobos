#!/usr/bin/env python3
"""
Generate CSV file containing ship data from EVE Frontier extracted JSON data.

Outputs ship attributes including structure, capacity, fuel, mass, volume, 
inertia, shield, capacitor, targeting, signature, scan resolution, velocity, and warp speed.

Usage:
    python generate_ship_csv.py [--output ship_data.csv] [--eve "C:\\path\\to\\EVE"]
"""

import argparse
import csv
import json
import os
import sys
from pathlib import Path


# Dogma attribute IDs mapped to their meanings
# These IDs are CCP's internal attribute identifiers
# Note: Some attributes (like cargo capacity, mass, volume) are stored directly in types.json, not in dogma
ATTRIBUTE_MAP = {
    # Structure and Combat
    'hp': 9,                          # Structure HP
    'fuelCapacity': 5633,             # Fuel capacity (units) - Frontier-specific
    
    # Physical Properties (from dogma)
    'inertiaModifier': 70,            # Inertia modifier
    
    # Shield and Capacitor
    'shieldRechargeRate': 479,        # Shield recharge time (milliseconds)
    'capacitorCapacity': 482,         # Capacitor capacity (GJ)
    
    # Heat Properties  
    'heatCapacity': 1271,             # Specific heat (C)
    'heatDissipation': 1132,          # Conductance (k)
    
    # Targeting
    'maxTargetRange': 76,             # Max targeting range (meters)
    'maxLockedTargets': 192,          # Max locked targets
    'signatureRadius': 552,           # Signature radius (meters)
    'scanResolution': 564,            # Scan resolution (mm)
    
    # Navigation
    'maxVelocity': 37,                # Max velocity (m/s)
    'warpSpeedMultiplier': 600,       # Warp speed multiplier (c)
}


def load_json_file(filepath):
    """Load and parse a JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {filepath}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {filepath}: {e}")
        return None


def get_attribute_value(type_dogma, attr_id, default=None):
    """Extract attribute value from typedogma data."""
    if not type_dogma:
        return default
    
    # typedogma structure: { "dogmaAttributes": [ {"attributeID": X, "value": Y}, ... ] }
    dogma_attrs = type_dogma.get('dogmaAttributes', [])
    for attr in dogma_attrs:
        if attr.get('attributeID') == attr_id:
            return attr.get('value', default)
    
    return default


def get_ship_class(group_name):
    """
    Determine ship class from group name.
    Maps EVE group names to simplified class names.
    """
    group_lower = group_name.lower()
    
    # Direct mappings
    class_map = {
        'shuttle': 'Shuttle',
        'corvette': 'Corvette',
        'frigate': 'Frigate',
        'destroyer': 'Destroyer',
        'cruiser': 'Cruiser',
        'battlecruiser': 'Battlecruiser',
        'battleship': 'Battleship',
        'capital': 'Capital',
        'supercarrier': 'Supercarrier',
        'titan': 'Titan',
        'dreadnought': 'Dreadnought',
        'carrier': 'Carrier',
        'freighter': 'Freighter',
        'industrial': 'Industrial',
        'mining barge': 'Mining Barge',
        'exhumer': 'Exhumer',
        'expedition frigate': 'Expedition Frigate',
        'logistics': 'Logistics',
        'command ship': 'Command Ship',
        'strategic cruiser': 'Strategic Cruiser',
        'tactical destroyer': 'Tactical Destroyer',
    }
    
    for key, value in class_map.items():
        if key in group_lower:
            return value
    
    # Check for specific patterns
    if 'combat' in group_lower:
        if 'battlecruiser' in group_lower:
            return 'Combat Battlecruiser'
        if 'frigate' in group_lower:
            return 'Combat Frigate'
    
    if 'attack' in group_lower:
        if 'battlecruiser' in group_lower:
            return 'Attack Battlecruiser'
        if 'cruiser' in group_lower:
            return 'Attack Cruiser'
    
    if 'heavy' in group_lower:
        if 'assault' in group_lower:
            return 'HAF'  # Heavy Assault Frigate
        if 'interdictor' in group_lower:
            return 'Heavy Interdictor'
    
    # Frontier-specific classes
    if 'usv' in group_lower or 'utility' in group_lower:
        return 'Frigate'
    if 'mcf' in group_lower or 'multi' in group_lower and 'combat' in group_lower:
        return 'Frigate'
    
    return group_name  # Return original if no match


def get_faction_name(type_data, factions_data):
    """
    Determine faction name from type data.
    Returns the faction name or 'Unknown' if not found.
    """
    # Try factionID from type data (for standard EVE factions)
    faction_id = type_data.get('factionID')
    if faction_id and str(faction_id) in factions_data:
        faction_info = factions_data[str(faction_id)]
        return faction_info.get('factionName_en-us', 'Unknown')
    
    # Frontier-specific: Check marketGroupID
    # Frontier factions are organized by market group
    market_group_id = type_data.get('marketGroupID')
    if market_group_id:
        # Known Frontier faction market group mappings
        frontier_market_groups = {
            3694: 'Exclave',
            3695: 'Synod',
            3749: 'Keep',
        }
        if market_group_id in frontier_market_groups:
            return frontier_market_groups[market_group_id]
    
    # Fallback: Try parsing from description
    description = type_data.get('description_en-us', '')
    
    # Frontier factions mentioned in descriptions
    frontier_factions = {
        'Keep': ['Keep'],
        'Synod': ['Synod'],
        'Exclave': ['Exclave'],
    }
    
    for faction, keywords in frontier_factions.items():
        for keyword in keywords:
            if keyword in description:
                return faction
    
    # Fallback: Try parsing from type name
    type_name = type_data.get('typeName_en-us', '')
    
    for faction, keywords in frontier_factions.items():
        for keyword in keywords:
            if keyword.lower() in type_name.lower():
                return faction
    
    return 'Unknown'


def is_ship_category(category_id, categories_data):
    """Check if category is Ship."""
    cat_info = categories_data.get(str(category_id), {})
    cat_name = cat_info.get('categoryName_en-us', '').lower()
    return 'ship' in cat_name


def is_ship_group(group_name):
    """
    Check if group represents a flyable ship.
    Excludes things like structures, deployables, etc.
    """
    group_lower = group_name.lower()
    
    # Ship keywords
    ship_keywords = [
        'shuttle', 'corvette', 'frigate', 'destroyer', 'cruiser',
        'battlecruiser', 'battleship', 'carrier', 'dreadnought',
        'titan', 'supercarrier', 'freighter', 'industrial',
        'mining barge', 'exhumer', 'capital', 'logistics',
        'command ship', 'strategic', 'assault', 'interceptor',
        'stealth', 'covert', 'electronic', 'force recon',
        'combat recon', 'heavy assault', 'marauder', 'black ops',
        'jump freighter', 'transport', 'blockade runner',
        'expedition', 'prospect', 'endurance', 'tactical'
    ]
    
    # Frontier-specific ship identifiers
    frontier_ships = ['usv', 'mcf', 'haf', 'lorha', 'tades', 'maul', 'chumaq']
    
    # Check for ship keywords
    for keyword in ship_keywords:
        if keyword in group_lower:
            return True
    
    # Check for Frontier ships
    for ship in frontier_ships:
        if ship in group_lower:
            return True
    
    return False


def generate_ship_csv(output_dir='output', output_file='ship_data.csv'):
    """
    Generate CSV file with ship data from extracted JSON files.
    
    Args:
        output_dir: Directory containing extracted JSON data
        output_file: Output CSV filename
    Returns:
        True on success, False on failure
    """
    output_path = Path(output_dir)
    
    # Load required data files
    print("Loading data files...")
    types_file = output_path / 'fsd_built' / 'types.json'
    groups_file = output_path / 'fsd_built' / 'groups.json'
    categories_file = output_path / 'fsd_built' / 'categories.json'
    typedogma_file = output_path / 'fsd_built' / 'typedogma.json'
    factions_file = output_path / 'fsd_built' / 'factions.json'
    
    # Check if files exist
    required_files = [types_file, groups_file, categories_file, typedogma_file]
    for file in required_files:
        if not file.exists():
            print(f"Error: Required file not found: {file}")
            print("\nPlease run data extraction first:")
            print('    python run.py --eve "C:\\CCP\\EVE Online" --json output --translate=multi')
            return False
    
    types_data = load_json_file(types_file)
    groups_data = load_json_file(groups_file)
    categories_data = load_json_file(categories_file)
    typedogma_data = load_json_file(typedogma_file)
    factions_data = load_json_file(factions_file) if factions_file.exists() else {}
    
    if not all([types_data, groups_data, categories_data, typedogma_data]):
        print("Error: Failed to load required data files")
        return False
    
    print(f"Loaded {len(types_data)} types, {len(groups_data)} groups, {len(categories_data)} categories")
    
    # Collect ship data
    ships = []
    
    for type_id, type_info in types_data.items():
        # Get group info
        group_id = type_info.get('groupID')
        if not group_id:
            continue
        
        group_info = groups_data.get(str(group_id), {})
        group_name = group_info.get('groupName_en-us', '')
        category_id = group_info.get('categoryID')
        
        # Check if this is a ship
        if not is_ship_category(category_id, categories_data):
            continue
        
        if not is_ship_group(group_name):
            continue
        
        # Check if published (exclude unpublished test items)
        if not type_info.get('published', 0):
            continue
        
        # Get type attributes
        ship_name = type_info.get('typeName_en-us', 'Unknown')
        type_dogma = typedogma_data.get(str(type_id), {})
        
        # Extract all attributes
        # Note: Some attributes come from types.json directly (capacity, volume, mass)
        # Others come from dogma attributes (hp, fuel, shields, etc.)
        ship_data = {
            'Faction': get_faction_name(type_info, factions_data),
            'ShipName': ship_name,
            'Class': get_ship_class(group_name),
            'StructureHP': get_attribute_value(type_dogma, ATTRIBUTE_MAP['hp'], 0),
            'Capacity_m3': type_info.get('capacity', 0),  # Direct from types.json
            'FuelCapacity_units': get_attribute_value(type_dogma, ATTRIBUTE_MAP['fuelCapacity'], 0),
            'Mass_kg': type_info.get('mass', 0),  # Direct from types.json
            'VolumeUnpackaged_m3': type_info.get('volume', 0),  # Direct from types.json
            'VolumePackaged_m3': type_info.get('packagedVolume', 0),  # Direct from types.json
            'InertiaModifier': get_attribute_value(type_dogma, ATTRIBUTE_MAP['inertiaModifier'], 0),
            'ShieldRecharge_s': get_attribute_value(type_dogma, ATTRIBUTE_MAP['shieldRechargeRate'], 0) / 1000,  # Convert ms to s
            'Capacitor_GJ': get_attribute_value(type_dogma, ATTRIBUTE_MAP['capacitorCapacity'], 0),
            'SpecificHeat_C': get_attribute_value(type_dogma, ATTRIBUTE_MAP['heatCapacity'], 0),
            'Conductance_k': get_attribute_value(type_dogma, ATTRIBUTE_MAP['heatDissipation'], 0),
            'MaxTargetRange_km': get_attribute_value(type_dogma, ATTRIBUTE_MAP['maxTargetRange'], 0) / 1000,  # Convert m to km
            'MaxLockedTargets': get_attribute_value(type_dogma, ATTRIBUTE_MAP['maxLockedTargets'], 0),
            'SignatureRadius_m': get_attribute_value(type_dogma, ATTRIBUTE_MAP['signatureRadius'], 0),
            'ScanResolution_mm': get_attribute_value(type_dogma, ATTRIBUTE_MAP['scanResolution'], 0),
            'MaxVelocity_mps': get_attribute_value(type_dogma, ATTRIBUTE_MAP['maxVelocity'], 0),
            'WarpSpeed_c': get_attribute_value(type_dogma, ATTRIBUTE_MAP['warpSpeedMultiplier'], 0),
        }
        
        # Only include ships with meaningful structure HP (excludes incomplete data)
        if ship_data['StructureHP'] > 0:
            ships.append(ship_data)
    
    # Sort by faction, then class, then ship name
    ships.sort(key=lambda x: (x['Faction'], x['Class'], x['ShipName']))
    
    print(f"\nFound {len(ships)} ships")
    
    # Write CSV
    if ships:
        csv_path = Path(output_file)
        fieldnames = [
            'Faction', 'ShipName', 'Class', 'StructureHP', 'Capacity_m3',
            'FuelCapacity_units', 'Mass_kg', 'VolumeUnpackaged_m3', 'VolumePackaged_m3',
            'InertiaModifier', 'ShieldRecharge_s', 'Capacitor_GJ',
            'SpecificHeat_C', 'Conductance_k', 'MaxTargetRange_km',
            'MaxLockedTargets', 'SignatureRadius_m', 'ScanResolution_mm',
            'MaxVelocity_mps', 'WarpSpeed_c'
        ]
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(ships)
        
        print(f"\n[OK] Ship data written to: {csv_path}")
        print(f"  Total ships: {len(ships)}")
        
        # Show sample
        print("\nSample ships:")
        for ship in ships[:5]:
            print(f"  - {ship['Faction']}: {ship['ShipName']} ({ship['Class']})")
        
        return True
    else:
        print("\n[WARN] No ships found in data")
        return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Generate CSV file with EVE ship data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Generate ship_data.csv from default output directory:
    python -m scripts.generate_ship_csv
    
  Specify custom output file:
    python -m scripts.generate_ship_csv --output my_ships.csv
    
  Use custom data directory:
    python -m scripts.generate_ship_csv --data-dir custom_output
        """
    )
    
    parser.add_argument(
        '--output', '-o',
        default='ship_data.csv',
        help='Output CSV filename (default: ship_data.csv)'
    )
    
    parser.add_argument(
        '--data-dir', '-d',
        default='output',
        help='Directory containing extracted JSON data (default: output)'
    )
    
    parser.add_argument(
        '--eve',
        help='EVE client path (if data extraction is needed)'
    )
    
    args = parser.parse_args()
    
    # Check if data directory exists
    data_path = Path(args.data_dir)
    if not data_path.exists():
        print(f"Data directory not found: {data_path}")
        
        if args.eve:
            print("\nRunning data extraction first...")
            import subprocess
            result = subprocess.run([
                sys.executable, '-m', 'run',
                '--eve', args.eve,
                '--json', args.data_dir,
                '--translate=multi'
            ])
            
            if result.returncode != 0:
                print("Error: Data extraction failed")
                sys.exit(1)
        else:
            print("\nPlease either:")
            print("  1. Run data extraction first:")
            print('     python -m run --eve "C:\\CCP\\EVE Online" --json output --translate=multi')
            print("  2. Or provide --eve argument to this script")
            sys.exit(1)
    
    # Generate CSV
    success = generate_ship_csv(args.data_dir, args.output)
    sys.exit(0 if success else 1)
