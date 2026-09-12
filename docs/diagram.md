---
config:
    maxEdges: 10000
    maxTextSize: 500000
    theme: dark
    layout: elk
---
flowchart TB

    %% Global Hierarchy
    B("Heuristics") --> n1{"Categories"}

    %% ----------------------------------------------------
    %% STAGE 0: POSITION PREREQUISITE FILTER
    %% ----------------------------------------------------
    n1 ==> n_filter["<b>Stage 0: Rank Filter</b><br>Filter active skills executable from hero current rank.<br>Discard unusable skills & apply invalidity penalty"]
    n_filter -.-> n6
    n_filter -.-> n7["Team synergy"]
    n1 --> n12["Trinkets"]

    %% ----------------------------------------------------
    %% SUBGRAPH 1: HERO UTILS & DESIRE VECTOR
    %% ----------------------------------------------------
    subgraph s1["Hero Utils"]
        n17["Manual data"] --> n18[("Hero desire vector")]
        n18 --> n25["Stats: DMG, SPD, ACC, CRIT, DODGE, PROT, HP, Resists, Skill Chances"]
        n18 --> n26["Global stats: Disease, Death Blow, Stress, Healing Recv, Virtue"]
    end

    %% ----------------------------------------------------
    %% SUBGRAPH 2: STAT CATEGORIES & SCALING
    %% ----------------------------------------------------
    subgraph s2["Stats Evaluation"]
        n88["Asses debuff strength<br>Similar logic to buff vector, but it's general for every type of enemy<br>That's why weighted sum/dot product is used"]
        n87["Evaluate healing output<br>Score total effective HP + bonus for AoE Death's Door clearance"]
        n80["Scale raw DPS by damage hyperparam, normalizing output close to 1"]
        n79["Calculate max raw dps for valid skill set"] --> n80
        n59_dmg@{ shape: "fr-rect", label: "DPS normalization hyperparam" }
        n59_heal@{ shape: "fr-rect", label: "Sum healing and divide by heal hyperparam, so value is close to 1" }
        n69@{ shape: "text", label: "Raw hero dps" }
        n6["Stat Category"] --> n11["Damage"]
        n6 --> n2["Healing"]
        n2 --> n87
        n6 --> n3["Self healing"]
        n6 --> n4["Buffs / Self debuffs"]
        n6 --> n5["Enemy debuffs"]
        n5 --> n88
        n3 --> n85@{ shape: "st-rect", label: "Scan for self healing heroes" } --> n86@{ shape: "div-rect", label: "Search for self heal in valid active skills" }
        n4 --> n83["Create buff vector (min-max scaled)"]
        n4 --> n84["Debuffs get negative values in buff vector"]
    end

    %% ----------------------------------------------------
    %% SUBGRAPH 3: TEAM SYNERGY
    %% ----------------------------------------------------
    subgraph s_syn["Team Synergy Analysis"]
        n92["Sum heroes with valid stun skills<br>Score coverage across enemy ranks R1-R4 + AoE coverage<br>Multiply by stun chance & normalize"]
        n93["Mark Theme Check:<br>Requires >= 1 applier and >= 1 consumer<br>Verify relative speed: SPD(Marker) > SPD(Consumer)<br>Bonus scales with mark consumer damage potential"]
        n94["For each enemy position calculate how many active skills reach this position and sum expected damage for this position<br><br>For now omit expected damage. Some abilities can apply dot damage or stuns, pull enemies from the back, push to back.<br><br>Scale based on total amount of skills"]
        n95["Make blight and bleed separate<br>Calculate rank-weighted Expected Value (EV = Dmg/rd * rds * Resist_Prob)<br>Option 1: Constrained Monotonic NN with tanh saturation<br>Option 2: Non-linear threshold transform into Bradley-Terry preference model"]
        n7 --> n8["Skill reachability"]
        n7 --> n13["Backline range"]
        n7 --> n14["Stuns"]
        n7 --> n16["Blight / Bleed"]
        n7 --> n10["Team theme"]
        n10 ==> n9["Skill complements"]
        n9 --> n89@{ shape: "lean-r", label: "Each skill can have coupled skills" }
        n90@{ label: "For now these skills are all that have bonuses against stunned enemies or marked<br><br>And they require stuns or mark from other heroes<br><br>This category results in a bonus depending on % of coupled skills" }
        n89 --> n90
        n8 --> n91["Evaluate rank reach and targeting bottlenecks across enemy lineup"]
        n14 --> n92
        n10 --> n93
    end

    %% ----------------------------------------------------
    %% TRINKETS ROUTING
    %% ----------------------------------------------------
    n12 --> n15["Stats"]
    n12 --> n22["Scouting, Surprises, Trap Disarm"]
    n12 --> n19["Special Cases & Conditions"]
    n12 --> n60{{"Crimson Court Trinkets"}}
    n12 --> n66{{"Color of Madness Trinkets"}}

    n15 --> n20["Based on hero desire vector"]
    n22 -- "Same for every hero" --> n23["Stat bonus via min-max scaling"]

    %% ----------------------------------------------------
    %% SUBGRAPH 4: SPECIAL CONDITION HANDLERS
    %% ----------------------------------------------------
    subgraph s_cond["Conditional Stat Rules"]
        n19 --> n21(["Torch level"])
        n21 -- ">75 Torch Assumed" --> n34["Calculate stats only for Torch > 75"]

        n19 --> n27["Ranged / Melee conditions"]
        n27 --> n28["Count as 0 if missing required skill type"]

        n19 --> n35["Enemy type conditions"]
        n35 --> n36["Lower scaling to normalize expected value"]

        n19 --> n37["Hero position conditions"]
        n37 --> n38["Lower scaling if hero skill set causes movement"]
        n38 -.- n39["*Simplified heuristic to avoid dynamic combat sim*"]

        n19 --> n42["Round-based conditions"]
        n42 --> n43["Custom scaling:<br>After R1: ~0.75 | On R1: ~0.25"]

        n19 --> n44["On Death's Door"]
        n44 --> n45["Heavily penalty / Minimal scaling"]

        n19 --> n54["vs Marked effect"]
        n54 --> n55["Lower scaling if Mark theme, else 0"]

        n19 --> n33["Penalty for HP below condition"]
        n19 --> n50["Ignore food effects"]
    end

    %% ----------------------------------------------------
    %% SUBGRAPH 5: BASE TRINKET EXCEPTIONS
    %% ----------------------------------------------------
    subgraph s_exceptions["Specific Item Exceptions"]
        n19 --> n46(["Restraining Padlock"]) --> n47["Custom fixed value"]
        n19 --> n48(["Camper's Helmet"]) --> n49["Ignore stress heal effect"]
        n19 --> n51(["Sickening Satchel"]) --> n52["Lower DMG scaling"] & n53["Set to 0 if no blight"]
        n19 --> n56(["Vvulf's Tassel"]) --> n57["Ignore +5% CRIT vs size 2"]
    end

    %% ----------------------------------------------------
    %% SUBGRAPH 6: CRIMSON COURT
    %% ----------------------------------------------------
    subgraph s_cc["Crimson Court Set Handling"]
        n60 --> n64(["Second Place Trophy"]) --> n65["Ignore: Camp heal bonus"]
        n60 --> n59_cc["Ignored Trinkets<br>(Technical / Low Performance)"]
        n59_cc --- n58(["Viscount's Spices"])
        n59_cc --- n61(["Baron's Lash"])
        n59_cc --- n62(["Countess' Fan"])
        n59_cc --- n63["Other trinkets (except sets)"]
    end

    %% ----------------------------------------------------
    %% SUBGRAPH 7: COLOR OF MADNESS
    %% ----------------------------------------------------
    subgraph s_com["Color of Madness Handling"]
        n66 --> n24["Acidic Husk Ichor"] --> n29["Ignore vs Husk effect"]
        n66 --> n30["Topshelf Tonic"] --> n31["Ignore +15 DODGE with Herbs"]
        n66 --> n41["Dirge For The Devoured"] --> n72["Ignore +25% DMG with Laudanum"]

        n66 --> n79_com["Ignored CoM Trinkets<br>(Technical Reasons)"]
        n79_com --- n67["Lens of the Comet"]
        n79_com --- n68["Crystal / Cluster Pendant"]
        n79_com --- n70["Coat Of Many Colors"]
        n79_com --- n71["Miller's Pipe"]
        n79_com --- n73["Smoking Skull"]
        n79_com --- n74["Keening Bolts"]
        n79_com --- n75["Non-Euclidean Hilt"]
        n79_com --- n76["Petrified Skull / Amulet"]
        n79_com --- n77["Heretical Passage"]
        n79_com --- n78["Prismatic Heart Crystal"]
        n79_com --- n32["Thirsting Blade"]
        n79_com --- n40["Huskfang Whistle"]
        n79_com --- n81["Mirror Shield"]
        n79_com --- n82["Icosahedric Musket Balls"]
    end

    %% Style Overrides
    style n18 fill:#1a1a1a,stroke:#888
    style s1 fill:#111111,stroke:#555
    style s2 fill:#111111,stroke:#555
    style s_syn fill:#111111,stroke:#555
    style s_cond fill:#111111,stroke:#555
    style s_exceptions fill:#111111,stroke:#555
    style s_cc fill:#111111,stroke:#555
    style s_com fill:#111111,stroke:#555
    style n39 stroke-dasharray: 3 3
    style n_filter fill:#222,stroke:#00aa88,stroke-width:2px
    n86
    n11
    n11 --- n69
    n86 --- n59_heal
    n87 --- n59_heal
    n69
    n69 --- n79
    n80 --- n59_dmg
    style n80 stroke-width:0.5px,stroke-dasharray:5 5
    style n79 stroke-width:0.5px,stroke-dasharray:5 5
    style n87 stroke-width:0.5px,stroke-dasharray:5 5
    style n88 stroke-width:0.5px,stroke-dasharray:5 5
    style n89 stroke-width:0.5px
    style n90 stroke-width:0px
    n13 --- n94
    n16 --- n95