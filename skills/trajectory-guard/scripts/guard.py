#!/usr/bin/env python3
import json, sys, pathlib

def main():
    if len(sys.argv) != 2:
        print('Usage: guard.py <run_dir>')
        sys.exit(1)
    run_dir = pathlib.Path(sys.argv[1])
    obs_path = run_dir / 'observations.json'
    traj_path = pathlib.Path('trajectory.md')
    if not obs_path.exists() or not traj_path.exists():
        print('Missing data for guard check')
        sys.exit(1)
    try:
        obs = json.loads(obs_path.read_text())
        with open(traj_path) as f:
            baseline = f.read().strip()
    except Exception as e:
        print('Error reading files', e)
        sys.exit(1)
    # Simple check: compare a key 'summary' if present
    if obs.get('summary', '').strip() != baseline:
        print('Drift detected')
        sys.exit(1)
    print('No drift')
    sys.exit(0)

if __name__ == '__main__':
    main()
