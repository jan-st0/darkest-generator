---
config:
  layout: dagre
---
flowchart TB
 subgraph s1["Hero Utils"]
        n17["Manual data"]
  end
    B("Heuristics") --> n1["Categories"]
    n1 -.- n6["Stat Category"]
    n6 --> n5["Enemy debuffs"] & n4["Buffs / Self debuffs"] & n3["Self healing"] & n2["Healing"] & n11["Damage"]
    n1 -.-> n7["Team synergy"]
    n7 --> n8["Skill reachability"] & n9["skill complemetns"] & n10["Team theme"] & n13["Backline range"] & n14["Stuns"] & n16["Blight / Bleed"]
    n10 ==> n9
    n1 --> n12["Trinkets"]
    n12 --> n15["Untitled Node"]
    n17 -- Vector representing befits --> n18["Hero desire vector"]

    n1@{ shape: diam}
    n6@{ shape: card}
    n7@{ shape: card}
    n12@{ shape: card}
    n18@{ shape: h-cyl}
    style n18 fill:#000000
    style s1 fill:#000000,stroke:#757575