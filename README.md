# Darkest Generator

A Python and Machine Learning engine for analyzing, vectorizing, and ranking team compositions and builds in *Darkest Dungeon*.

The project models game mechanics into structured vector representations, accounts for positional skill viability during dynamic hero movement, and learns team-synergy heuristics from pairwise comparison data via a Bradley-Terry logistic ranking model.

---

## Key Features

- **Domain Modeling & Position Graph Traversal**: Models hero combat skills, stats, and trinkets. Uses depth-limited permutation graph traversal to evaluate dynamic active skills enabled by movement skills (e.g., Lunge, Duelist's Advance).
- **19-Dimensional Team Feature Vectorizer**: Translates a 4-hero party into a normalized vector capturing party/self healing, raw DPS, backline reach, rank coverage, crowd control (stun/bleed/blight), conditional synergies (Marked / Stunned combos), and contextual trinket valuation.
- **Context-Aware Trinket Evaluator**: Scores trinkets dynamically against hero stat desire vectors, item restrictions, condition scaling (torch levels, combat position stability), and Crimson Court item sets.
- **Pairwise ML Ranker (Bradley-Terry Formulation)**: Fits a logistic ranking model over team feature difference vectors $(\mathbf{x}_A - \mathbf{x}_B)$ using BFGS optimization with L2 regularization to score arbitrary party compositions.
- **FastAPI Service**: Provides endpoints for manual team evaluation, feature preview, and model scoring inference.

---

## Architecture Overview

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
      (Bradley-Terry ML Weights)            (/preview_party, /ranker/score)

```

---

## Tech Stack

* **Core**: Python, NumPy, SciPy, Scikit-learn, Pandas
* **API & Schemas**: FastAPI, Pydantic, Uvicorn
* **Data & Configuration**: PyYAML, Pickle

---

### Installation

Clone repository and install required packages.
You can use this command.

```bash
pip install -r pyproject.toml

```

### Usage

#### 1. Start the API Service

```bash
python main.py -ps

```

Interactive documentation is available at `http://localhost:8000/docs`.

#### 2. Train the Pairwise Ranking Model

Trains the regression ranker on unique labeled match-ups stored in `data/party_comparison.jsonl`:

```bash
# Train model and export artifact to models/ranker.pkl
python main.py -r

# Train and view convergence loss plot
python main.py -r --show-plot

```

---
## Planned Features

* [ ] **Genetic Algorithm Optimization**: Evolutionary search over a user-defined pool of heroes and trinkets to output Pareto-optimal team loadouts.
* [ ] **Automated Testing Suite**: Migrate diagnostic routines in `tmp_tests/` to automated unit and regression tests with `pytest`.
* [ ] **Save File & Roster Synchronization**: Directly ingest player roster and trinket inventories from game save files.
* [ ] **Deployment & Observability**: Docker containerization, structured logging, and health metrics.
