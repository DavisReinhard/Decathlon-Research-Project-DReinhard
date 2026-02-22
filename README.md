# Beyond Points: Event–Placing Alignment in NCAA Division I Decathlons (Scoring-Table-Free)

A scoring-table-free analysis of which decathlon events best align with final overall placing in NCAA Division I conference championships (Big Ten, SEC, ACC, Big12).

## Overview
This project examines which decathlon events most consistently align with **final overall placing** in **NCAA Division I conference championship** decathlons, without using scoring-table points as predictor inputs. The goal is a competition-relevant view of event alignment that can support **training emphasis** and **meet strategy**, while avoiding conclusions that may be partly driven by scoring-table conversion structure.

## Research Questions
- **RQ1 (Rank alignment):** Among top-eight finishers who completed all ten events, which event placings align most strongly with final overall placing?
- **RQ2 (Performance alignment):** Among top-eight finishers who completed all ten events, which events’ within-meet **z-scores** align most strongly with final overall placing?
- **RQ3 (Stability across conferences):** How does event–final placing alignment vary across the Big Ten, SEC, ACC, and Big 12 using (a) Spearman correlations on placings and (b) Pearson correlations on z-scores?

## Data & Scope
- **Population:** Men’s NCAA Division I conference championship decathlons (Big Ten, SEC, ACC, Big 12)
- **Unit of analysis:** Athlete–meet observation
- **Inclusion:** Top-eight overall finishers who completed all ten events
- **Outcome:** Final overall placing (1–8)
- **Predictors:** (a) event placing; (b) within-meet z-scores of raw event marks (direction-aligned so higher = better)
- **Exclusions:** Any athlete/meet with incomplete marks (e.g., DNS, DNF, NH, NT, NM)
- **Data format:** Meet-level CSV files (conference/year, athlete, final placing, and raw marks for all ten events)
