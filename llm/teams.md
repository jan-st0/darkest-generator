Here are 5 concrete, pre-built test cases covering the entire scoring spectrum (from near-unplayable disaster comps to tournament-grade meta). Each test case targets a specific evaluation axis (position locking, dynamic rank dancing, SPD-tier ordering, trinket anti-synergies, and burst setup) to stress-test whether your model actually calculates mechanics or just hallucinates synergy.

---

### Test Case 1: The "Grand Dance" (High Skill Ceiling / Dynamic Ranks)

* **Target Score:** **8.8 – 9.2**
* **Core Test:** Can the model calculate movement skill rotations (Holy Lance pushing back Grave Robber, Lunge pulling forward, Shadow Fade resetting) and understand how trinket SPD modifies turn order to make a dance engine consistent?

**Loadout (All items up to Very Rare / Unique):**

| Position | Hero | Skills | Trinkets |
| --- | --- | --- | --- |
| **Pos 4** | **Grave Robber** (Base SPD: 8) | Lunge, Shadow Fade, Thrown Dagger, Pick to the Face | *Raider's Talisman*, *Ancestor's Pen* |
| **Pos 3** | **Crusader** (Base SPD: 1) | Holy Lance, Smite, Inspiring Cry, Stunning Blow | *Focus Ring*, *Quick Draw Charm* |
| **Pos 2** | **Occultist** (Base SPD: 6) | Hands from the Abyss, Vulnerability Hex, Wyrd Reconstruction, Weakening Curse | *Demon's Cauldron*, *Vial of Sand* |
| **Pos 1** | **Bounty Hunter** (Base SPD: 5) | Collect Bounty, Flashbang, Finish Him, Uppercut | *Hunter's Talons*, *Wounding Helmet* |

* **What to grade the model on:**
* Round 1 opener: GR (high SPD + *Raider's Talisman*) opens with *Lunge* from Pos 4 $\rightarrow$ lands in Pos 2, pushing Occultist to 3 and Crusader to 4.
* Crusader gets +8 SPD R1 from *Quick Draw Charm*, guaranteeing he acts before heavy frontline monsters to cast *Holy Lance* from Pos 4 $\rightarrow$ moves to Pos 3, pushing GR back to Pos 3 for another *Lunge*.
* High-tier stun lockdown via Pos 2 Occultist (*Demon's Cauldron* + *Hands from the Abyss* = 180% stun chance) enabling BH's *Finish Him* bonus DMG.



---

### Test Case 2: The "Trinket Self-Sabotage" Trap (Good Positions, Ruined Math)

* **Target Score:** **4.8 – 5.2**
* **Core Test:** Can the model detect that while the positions and skills look completely standard, the equipped trinkets actively disable or penalize the heroes' specific loaded skill mechanics?

**Loadout (All items up to Very Rare / Crystalline):**

| Position | Hero | Skills | Trinkets |
| --- | --- | --- | --- |
| **Pos 4** | **Occultist** | Vulnerability Hex, Weakening Curse, Wyrd Reconstruction, Abyssal Artillery | *Petrified Skull*, *Cleansing Crystal* |
| **Pos 3** | **Houndmaster** | Target Whistle, Hound's Rush, Cry Havoc, Guard Dog | *Spiked Collar*, *Ancestor's Scroll* |
| **Pos 2** | **Bounty Hunter** | Collect Bounty, Flashbang, Come Hither, Finish Him | *Wounding Helmet*, *Brawler's Gloves* |
| **Pos 1** | **Flagellant** | Punish, Rain of Sorrows, Redeem, Exsanguinate | *Resurrection's Collar*, *Punishment's Hood* |

* **What to grade the model on:**
* **Occultist:** *Cleansing Crystal* gives -15% Debuff/Bleed skill (crippling Hex/Curse debuffs and lowering Wyrd bleed chance, but wasting debuff potential). *Petrified Skull* lowers Heal Recv by 20%.
* **Houndmaster:** *Spiked Collar* (-50% Heal Skills) directly neutralizes the +25% Stress/Heal from *Ancestor's Scroll*.
* **Bounty Hunter:** *Wounding Helmet* gives -20% Stun Skill & -25% Move Skill (ruining *Flashbang* and *Come Hither*), while *Brawler's Gloves* (+25% DMG in Pos 1) provides **zero** benefit in Pos 2.
* **Flagellant:** *Resurrection's Collar* (+33% Heal, -15% Bleed) and *Punishment's Hood* (+20% Bleed, -20% Heal) cancel each other out while imposing net stat loss.



---

### Test Case 3: The "Frontline Traffic Jam" (Positional Hard-Lock)

* **Target Score:** **1.5 – 2.0**
* **Core Test:** Does the model catch that 3 out of 4 heroes have their primary tools disabled because pure frontline melee heroes are shoved into the back ranks with no forward mobility?

**Loadout (Common / Uncommon Trinkets):**

| Position | Hero | Skills | Trinkets |
| --- | --- | --- | --- |
| **Pos 4** | **Flagellant** | Punish, Rain of Sorrows, Exsanguinate, Redeem | *Punishment's Hood*, *Heartburst Hood* |
| **Pos 3** | **Crusader** | Smite, Zealous Accusation, Stunning Blow, Bulwark of Faith | *Defender's Seal*, *Swordsman's Crest* |
| **Pos 2** | **Grave Robber** | Pick to the Face, Shadow Fade, Poison Dart, Toxin Trickery | *Sickening Satchel*, *Quickening Satchel* |
| **Pos 1** | **Occultist** | Abyssal Artillery, Vulnerability Hex, Weakening Curse, Sacrificial Stab | *Archer's Ring*, *Eldritch Killing Incense* |

* **What to grade the model on:**
* **Pos 4 Flagellant:** 100% disabled. *Punish*, *Rain of Sorrows*, and *Exsanguinate* require Pos 1–2. *Redeem* requires <40% HP (unusable at start). Flagellant has **zero legal actions** on Turn 1 and must Pass or Move.
* **Pos 3 Crusader:** *Smite*, *Accusation*, *Stunning Blow*, and *Bulwark* all require Pos 1–2. Crusader did not equip *Holy Lance*, leaving him with **zero legal attacks**.
* **Pos 1 Occultist:** Fragile HP pool (19 base) in rank 1. Equipped *Abyssal Artillery* (only launches from Pos 3–4) and *Archer's Ring* (+5 Ranged ACC) while holding melee *Sacrificial Stab*.



---

### Test Case 4: The Mark-Focus Meatgrinder (Optimal Meta Burst)

* **Target Score:** **9.5 – 9.8**
* **Core Test:** Can the model recognize a textbook high-tier meta composition that features synchronized SPD tiers, PROT debuffing, dual stun, stress relief, and high-accuracy mark execution?

**Loadout (Endgame / Ancestral / Boss Trophies):**

| Position | Hero | Skills | Trinkets |
| --- | --- | --- | --- |
| **Pos 4** | **Houndmaster** (Base SPD: 5) | Hound's Rush, Target Whistle, Cry Havoc, Blackjack | *Prophet's Eye*, *Ancestor's Musket Ball* |
| **Pos 3** | **Occultist** (Base SPD: 6) | Vulnerability Hex, Wyrd Reconstruction, Abyssal Artillery, Weakening Curse | *Demon's Cauldron*, *Ancestor's Pistol* |
| **Pos 2** | **Bounty Hunter** (Base SPD: 5) | Collect Bounty, Mark for Death, Flashbang, Finish Him | *Vvulf's Tassle*, *Focus Ring* |
| **Pos 1** | **Crusader** (Base SPD: 1) | Smite, Stunning Blow, Inspiring Cry, Battle Heal | *Ancestor's Signet Ring*, *Commander's Orders* |

* **What to grade the model on:**
* **Turn Order Logic:** Occultist has +3 SPD (*Ancestor's Pistol* $\rightarrow$ 9 SPD) guaranteeing fastest turn $\rightarrow$ casts *Vulnerability Hex* (-20 DODGE + Mark).
* **Payoff:** Houndmaster (*Prophet's Eye* Pos 4 buff + *Musket Ball*) and Bounty Hunter (*Vvulf's Tassle* +20% DMG / +10 ACC vs Marked) delete rank 2, 3, or 4 enemies before they act.
* **Sustain Balance:** Crusader acts as off-healer and stress relief (*Commander's Orders* boosts *Battle Heal* by +33%), while Occultist provides spot emergency healing and HM handles AoE stress.



---

### Test Case 5: The "One-Trick Bleed" (Functional but Narrow)

* **Target Score:** **6.2 – 6.5**
* **Core Test:** Can the model evaluate a team that functions reliably in a specific biome (Warrens/Courtyard) but has severe vulnerabilities: zero reliable stress healing, low direct damage, zero blight options, and heavy reliance on high-variance heals?

**Loadout (Uncommon / Rare Trinkets):**

| Position | Hero | Skills | Trinkets |
| --- | --- | --- | --- |
| **Pos 4** | **Occultist** | Wyrd Reconstruction, Vulnerability Hex, Daemons Pull, Weakening Curse | *Cursed Incense*, *Chirurgeon's Charm* |
| **Pos 3** | **Houndmaster** | Hound's Harry, Hound's Rush, Target Whistle, Guard Dog | *Cudgel Weight*, *Bleed Amulet* |
| **Pos 2** | **Houndmaster** | Hound's Rush, Hound's Harry, Blackjack, Guard Dog | *Agility Whistle*, *Stun Amulet* |
| **Pos 1** | **Flagellant** | Punish, Rain of Sorrows, Reclaim, Suffer | *Bleed Amulet*, *Blood Charm* |

* **What to grade the model on:**
* **Strengths Identified:** Massive stacking bleed damage (Flagellant *Punish* + *Rain of Sorrows*, double HM *Hound's Harry*). Strong rank 1–3 stun control via Pos 2 HM *Blackjack* (+Stun Amulet).
* **Weaknesses Identified:** Zero active stress healing (neither Houndmaster has *Cry Havoc* equipped; Crusader/Jester absent). Fragile health recovery entirely reliant on *Wyrd Reconstruction* (variance) and Flagellant *Reclaim*. Complete lack of Armor-Piercing (AP) or Blight for high-PROT / Bleed-immune enemies (Ruins/Cove).



---

### Evaluation Criteria Matrix for Your Model

Feed each test case into your local LLM and verify it passes these checks:

1. **Positional Legality:** Did it correctly identify whether all 4 skills per hero can be cast from their assigned position?
2. **Trinket Synergy:** Did it catch useless trinket passives (e.g., *Brawler's Gloves* in Pos 2) or detrimental interactions (e.g., *Cleansing Crystal* debuff penalty on Occultist)?
3. **Action Economy & Turn Order:** Did it evaluate who moves first based on Base SPD + Trinket SPD mods?
4. **Sustain Check:** Did it evaluate both HP recovery and Stress recovery capacity?