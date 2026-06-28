#!/usr/bin/env python3
"""Unified build orchestrator for Phobos data extraction and generation."""

import argparse
import os
import sys


def _run_step(name, func):
    """Execute a pipeline step and abort with a clear message on failure."""
    print("=" * 60)
    print(f"Running: {name}")
    print("=" * 60)
    try:
        result = func()
        # Some steps return nonzero exit codes rather than raising
        if isinstance(result, int) and result != 0:
            raise RuntimeError(f" exited with code {result}")
        if result is False:
            raise RuntimeError(" returned failure")
    except Exception as e:
        print(f"\n[ERROR] Step '{name}' failed: {e}")
        raise RuntimeError(f"Pipeline aborted because step '{name}' failed") from e


def run_pipeline(eve, output, server='stillness', translate='multi', list_filter=''):
    raw_dir = os.path.join(output, 'raw')
    os.makedirs(raw_dir, exist_ok=True)
    print(f"Output base: {output}")
    print(f"Raw data dir: {raw_dir}")

    # 1. Upstream extraction
    import run
    _run_step(
        'run (upstream extraction)',
        lambda: run.run(
            path_eve=eve,
            server_alias=server,
            filter_string=list_filter,
            language=translate,
            path_json=raw_dir,
        )
    )

    # 2. Generate universe database
    from scripts import generate
    db_path = os.path.join(output, 'eve_universe.db')
    _run_step(
        'generate (universe DB)',
        lambda: generate.main(output=db_path, phobos_output=raw_dir, query=None),
    )

    # 3. Generate ship CSV
    from scripts import generate_ship_csv
    csv_path = os.path.join(output, 'ship_data.csv')
    _run_step(
        'generate_ship_csv (ship CSV)',
        lambda: generate_ship_csv.generate_ship_csv(output_file=csv_path, output_dir=raw_dir),
    )

    # 4. Extract item icons
    from scripts import generate_image_zip
    _run_step(
        'generate_image_zip (item icons)',
        lambda: generate_image_zip.main(eve=eve, output=raw_dir, server=server, verbose=False),
    )

    # 5. Extract landscapes
    from scripts import extract_landscapes
    _run_step(
        'extract_landscapes (landscapes)',
        lambda: extract_landscapes.main(output_dir=raw_dir),
    )

    print("\n" + "=" * 60)
    print("Build complete. Artifacts in:", output)
    print("=" * 60)
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Run the full Phobos extraction and generation pipeline.',
        epilog='Example: python -m scripts.build_all --eve "C:\\CCP\\EVE Frontier" --output ./out'
    )
    parser.add_argument('--eve', required=True, help='Path to EVE client folder')
    parser.add_argument('--output', '-o', required=True, help='Output directory')
    parser.add_argument('--server', default='stillness', help='Server alias (default: stillness)')
    parser.add_argument('--translate', default='multi', help='Translation mode (default: multi)')
    parser.add_argument('--list', default='', help='Comma-separated container filter')
    args = parser.parse_args()

    try:
        sys.exit(run_pipeline(args.eve, args.output, args.server, args.translate, args.list))
    except KeyboardInterrupt:
        print("\nAborted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nPipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
