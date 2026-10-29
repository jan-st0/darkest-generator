# Darkest Generator

A Python tool and machine learning model that analyzes, scores, and ranks team builds for *Darkest Dungeon*.

---

## The Game: *Darkest Dungeon*

*Darkest Dungeon* is a tactical turn-based RPG centered around positional combat:

* Teams consist of four heroes lined up in ranks 1 to 4 (front to back).


* Combat skills are rank-restricted: they can only be used from specific positions and can only hit specific enemy ranks.


* Movement skills push or pull heroes during combat, dynamically changing their ranks and deciding which abilities remain usable.


* Effective teams require balancing position stability, status effects (Stun, Mark, Bleed, Blight), and stat-boosting trinkets.



## What This Project Does

Building a solid team requires tracking dozens of moving parts. This project automates that analysis and ranks setups using machine learning:

* **Tracks Skill Usability Across Ranks:** Simulates rank shifts caused by movement skills (up to 3 turns deep) to find every rank a hero can reach and filter out unusable skills.


* **Turns Teams into 19 Measurable Stats:** Converts a 4-hero setup—including base stats, active skills, trinkets, and synergies—into a normalized 19-number vector.


* **Ranks Builds with Machine Learning:** Uses a pairwise comparison model (Team A vs. Team B) trained with logistic regression and BFGS optimization to predict an overall score for any team.


* **Serves Real-Time Insights:** Provides a FastAPI service to inspect active skills, reachable positions, team synergy breakdowns, and composite scores.



---

## Key Features

* **Hero Movement & Skill Verification:** Recursively checks rank swaps (e.g., Highwayman's *Duelist's Advance* or Grave Robber's *Lunge*) to determine which skills actually stay active during a battle.


* **19-Metric Team Vector:** Evaluates damage output, healing, backline threat reach, stun/DoT coverage, and combo readiness (such as pairing Mark appliers with Mark consumers).


* **Context-Aware Trinket Scoring:** Evaluates trinkets based on whether their stat bonuses match a hero's primary role, position requirements, and team status conditions.


* **Pairwise Ranking Model:** Learns feature weights from head-to-head match-up comparisons stored in JSONL format, producing a single quality rating for any lineup.


* **FastAPI Endpoints:** Clean REST endpoints for evaluating party builds, inspecting vectors, and running model inference.



---

## Architecture

```text
                        +----------------------------+
                        |  darkest_dungeon_data.yml  |
                        +--------------+-------------+
                                       |
                              [Domain Parsing]
                                       v
+------------------+         +-------------------+
|  Party Request   | ------> |    Party Model    |
| (4 Heroes, Ranks,|         | (Permutation &    |
| Skills, Trinkets)|         | Skill Resolution) |
+------------------+         +---------+---------+
                                       |
                                       v
                             [Party Vectorizer]
                                       |
                   +-------------------+-------------------+
                   |                                       |
                   v                                       v
           [Ranker / Scorer]                       [FastAPI Service]
         (ML Ranking Weights)               (/preview_party, /ranker/score)

```



---

## Tech Stack

* **Language:** Python


* **Machine Learning & Math:** scikit-learn, SciPy, NumPy, Pandas


* **Web API & Validation:** FastAPI, Uvicorn, Pydantic


* **Data & Plots:** PyYAML, Matplotlib



---

## Getting Started

### 1. Installation

Clone the repository and install the project in editable mode:

```bash
git clone <repo-url>
cd darkest-generator
pip install -e .

```

*(Dependencies: `fastapi`, `uvicorn`, `pydantic`, `numpy`, `scipy`, `scikit-learn`, `pandas`, `PyYAML`, `matplotlib`)*

### 2. Run the API Server

Start the local FastAPI server:

```bash
python main.py -ps

```

Interactive Swagger documentation will be available at `http://localhost:8000/docs`.

### 3. Train the Ranking Model

Train the pairwise ranking model on labeled comparison data from `data/party_comparison.jsonl` and export the model to `models/ranker.pkl`:

```bash
# Train and save the model
python main.py -r

# Train and view the loss plot interactively
python main.py -r --show-plot

```



---

## API Overview

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/ranker/score` | Returns a quality score for a 4-hero team using the trained model.

 |
| `POST` | `/team_comparison/preview_party` | Returns active skills, reachable ranks, and the 19-stat vector for a team.

 |
| `POST` | `/team_comparison/create_new` | Saves a new pairwise team comparison to the training dataset.

 |
| `GET` | `/team_comparison/all_heroes/` | Lists all 18 available hero classes.

 |
| `GET` | `/team_comparison/game_data_bundle/` | Returns base stats, skills, and trinkets in a single payload.

 |

---

## Planned Features

* [ ] **Genetic Algorithm Team Generator:** Run evolutionary searches across hero and trinket pools to find top-tier team builds automatically.


* [ ] **Automated Test Suite:** Migrate existing test scripts in `tmp_tests/` into standard `pytest` unit test suites.


* [ ] **Save File Sync:** Import hero rosters and trinket inventories directly from game save files.


* [ ] **Containerization:** Add Docker support and structured logging.
