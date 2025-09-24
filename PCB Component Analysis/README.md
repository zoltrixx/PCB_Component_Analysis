# PCB Component Placement - Assignment Solution

## Description
This project implements a constraint-aware algorithm to place five rectangular components
(USB, MCU, CRYSTAL, MB1, MB2) on a 50×50 PCB grid satisfying specified hard constraints:
- Edge placement for USB and both MikroBus connectors.
- MikroBus connectors on opposite edges and parallel.
- Crystal within 10 units of MCU center.
- No overlaps, components remain inside board boundaries.
- Center of mass within 2.0 units of board center.
- Crystal-to-MCU straight path must not intersect the USB keep-out zone.

Soft constraints (minimize wasted space, prefer central placement) are taken into account by a simple score.

## Files
- `main.py` — program that searches for a solution, plots it, and writes a summary.
- `requirements.txt` — required Python packages.
- `README.md` — this file.

## How to run
1. Install dependencies:
2. Run:
3. If a solution is found, outputs will be saved to:
- `/mnt/data/pcb_solution.png` (plot)
- `/mnt/data/pcb_solution_summary.txt` (text summary)

## Tuning
- To increase the search aggressiveness, open `main.py` and increase `TIME_LIMIT` in `main()`.
- To try different randomness, change the `seed` passed to `find_solution()`.

## Notes
- The script uses a randomized, constraint-aware search that is tuned to be fast. If no solution is found within the default time, try increasing the time limit or randomization seed.
