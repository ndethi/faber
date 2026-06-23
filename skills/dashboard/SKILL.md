# Dashboard Skill

> Generates a simple HTML dashboard aggregating run observations and feedback.

## Overview
The **dashboard** skill scans the  directory, collects each run's  and  (if present), and produces an HTML file  showing a table of runs, costs, and ratings.

## Specification
- Input: none (operates on the repository root).
- Walks  directories.
- For each run, extracts , ,  from  and  from .
- Writes a static HTML page with a table of the collected data.

## Implementation
Implemented in .
