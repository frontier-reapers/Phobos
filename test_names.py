#!/usr/bin/env python3

import sqlite3

def test_localized_names():
    conn = sqlite3.connect('eve_universe.db')
    cursor = conn.cursor()

    # Look for system ID 30009299 (should be I4F-MCH now)
    cursor.execute('SELECT solarSystemId, name FROM SolarSystems WHERE solarSystemId = 30009299')
    result = cursor.fetchone()
    if result:
        print(f'Found system 30009299: ID={result[0]}, Name="{result[1]}"')
    else:
        print('System 30009299 not found')

    # Check for I4F-MCH by name
    cursor.execute('SELECT solarSystemId, name, constellationId FROM SolarSystems WHERE name = ?', ('I4F-MCH',))
    result = cursor.fetchone()
    if result:
        print(f'Found I4F-MCH: {result}')
    else:
        print('I4F-MCH not found by name')

    # Show some sample systems to see the names
    cursor.execute('SELECT solarSystemId, name FROM SolarSystems LIMIT 10')
    print('\nSample systems with localized names:')
    for row in cursor.fetchall():
        print(f'  {row[0]}: {row[1]}')

    # Count how many systems have real names vs generic names
    cursor.execute('SELECT COUNT(*) FROM SolarSystems WHERE name NOT LIKE ?', ('System %',))
    named_systems = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM SolarSystems')
    total_systems = cursor.fetchone()[0]
    print(f'\nSystems with real names: {named_systems} out of {total_systems}')

    # Check for NULL or empty names
    cursor.execute('SELECT COUNT(*) FROM SolarSystems WHERE name IS NULL OR name = ?', ('',))
    null_systems = cursor.fetchone()[0]
    print(f'Systems with NULL/empty names: {null_systems}')

    # Check regions for generic names
    cursor.execute('SELECT COUNT(*) FROM Regions WHERE name LIKE ?', ('Region %',))
    generic_regions = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM Regions')
    total_regions = cursor.fetchone()[0]
    print(f'Regions with generic names: {generic_regions} out of {total_regions}')

    # Check constellations for generic names
    cursor.execute('SELECT COUNT(*) FROM Constellations WHERE name LIKE ?', ('Constellation %',))
    generic_constellations = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM Constellations')
    total_constellations = cursor.fetchone()[0]
    print(f'Constellations with generic names: {generic_constellations} out of {total_constellations}')

    # Show some sample regions
    cursor.execute('SELECT regionId, name FROM Regions LIMIT 5')
    print('\nSample regions:')
    for row in cursor.fetchall():
        print(f'  {row[0]}: {row[1]}')

    # Show some sample constellations
    cursor.execute('SELECT constellationId, name FROM Constellations LIMIT 5')
    print('\nSample constellations:')
    for row in cursor.fetchall():
        print(f'  {row[0]}: {row[1]}')

    conn.close()

if __name__ == '__main__':
    test_localized_names()
