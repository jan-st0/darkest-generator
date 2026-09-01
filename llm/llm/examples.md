### Few-Shot Examples

#### Example 1: Meta Mark & Stun Lockdown (High Tier)

**Input Party:**

* **Pos 4: Houndmaster** | Skills: `[Hound's Rush, Target Whistle, Cry Havoc, Guard Dog]` | Trinkets: `[Prophet's Eye, Ancestor's Musket Ball]`
* **Pos 3: Occultist** | Skills: `[Vulnerability Hex, Wyrd Reconstruction, Weakening Curse, Abyssal Artillery]` | Trinkets: `[Demon's Cauldron, Ancestor's Pistol]`
* **Pos 2: Bounty Hunter** | Skills: `[Collect Bounty, Flashbang, Finish Him, Uppercut]` | Trinkets: `[Vvulf's Tassle, Focus Ring]`
* **Pos 1: Crusader** | Skills: `[Smite, Stunning Blow, Inspiring Cry, Battle Heal]` | Trinkets: `[Ancestor's Signet Ring, Commander's Orders]`

**Evaluation Output:**

```json
{
  "positional_legality": {
    "pos_4_houndmaster": "Valid (All 4 skills launch from Pos 4)",
    "pos_3_occultist": "Valid (All 4 skills launch from Pos 3)",
    "pos_2_bounty_hunter": "Valid (All 4 skills launch from Pos 2)",
    "pos_1_crusader": "Valid (All 4 skills launch from Pos 1)",
    "subscore": 3.0
  },
  "synergy_and_mechanics": {
    "speed_tiers": "Occultist (SPD 9 with Pistol) acts first to apply Vulnerability Hex (-20 DODGE + Mark).",
    "damage_combos": "Pos 4 HM and Pos 2 BH deal massive burst vs Marked targets. High backline reach via Abyssal Artillery and Hound's Rush.",
    "crowd_control": "Dual heavy stuns: Pos 3 Occultist (Hands disabled, but BH Flashbang + Crusader Stunning Blow provide 140%+ stun coverage).",
    "subscore": 2.8
  },
  "trinket_compatibility": {
    "pos_4_houndmaster": "Optimal: Prophet's Eye grants +15 ACC, +3 SPD in Pos 4; Musket Ball boosts Ranged DMG/CRIT.",
    "pos_3_occultist": "Optimal: Ancestor's Pistol gives +15 Ranged ACC & +3 SPD for turn priority.",
    "pos_2_bounty_hunter": "Optimal: Vvulf's Tassle grants +20% DMG/+10 ACC vs Marked; Focus Ring secures ACC cap.",
    "pos_1_crusader": "Optimal: Commander's Orders buffs Battle Heal by +33% without compromising tanking stats.",
    "subscore": 2.0
  },
  "sustain_and_recovery": {
    "hp_sustain": "Crusader Battle Heal (boosted) provides consistent baseline; Occultist Wyrd Reconstruction provides emergency high burst.",
    "stress_sustain": "Crusader Inspiring Cry + Houndmaster Cry Havoc provides dual single-target and AoE stress relief.",
    "subscore": 1.9
  },
  "final_score": 9.7
}

```

---

#### Example 2: The "Trinket Sabotage" Mid-Tier (Decent Skills, Broken Stats)

**Input Party:**

* **Pos 4: Occultist** | Skills: `[Vulnerability Hex, Weakening Curse, Wyrd Reconstruction, Abyssal Artillery]` | Trinkets: `[Petrified Skull, Cleansing Crystal]`
* **Pos 3: Houndmaster** | Skills: `[Target Whistle, Hound's Rush, Cry Havoc, Guard Dog]` | Trinkets: `[Spiked Collar, Ancestor's Scroll]`
* **Pos 2: Bounty Hunter** | Skills: `[Collect Bounty, Flashbang, Come Hither, Finish Him]` | Trinkets: `[Wounding Helmet, Brawler's Gloves]`
* **Pos 1: Flagellant** | Skills: `[Punish, Rain of Sorrows, Redeem, Exsanguinate]` | Trinkets: `[Resurrection's Collar, Punishment's Hood]`

**Evaluation Output:**

```json
{
  "positional_legality": {
    "pos_4_occultist": "Valid (All 4 skills launch from Pos 4)",
    "pos_3_houndmaster": "Valid (All 4 skills launch from Pos 3)",
    "pos_2_bounty_hunter": "Valid (All 4 skills launch from Pos 2)",
    "pos_1_flagellant": "Valid (All 4 skills launch from Pos 1)",
    "subscore": 3.0
  },
  "synergy_and_mechanics": {
    "speed_tiers": "Standard SPD scaling. Occultist/Houndmaster can mark for Bounty Hunter.",
    "damage_combos": "Core Mark synergy is present, but CC payoff is undermined by debuffs on BH stun skills.",
    "crowd_control": "Flashbang stun chance reduced by trinket penalties.",
    "subscore": 1.8
  },
  "trinket_compatibility": {
    "pos_4_occultist": "Severe Conflict: Cleansing Crystal inflicts -15% Debuff Skill (cripples Hex/Curse). Petrified Skull reduces Heal Recv by 20%.",
    "pos_3_houndmaster": "Severe Conflict: Spiked Collar (-50% Heal Skills) cancels out Ancestor's Scroll (+25% Heal/Stress Skills).",
    "pos_2_bounty_hunter": "Severe Conflict: Wounding Helmet gives -20% Stun & -25% Move (ruins Flashbang/Come Hither). Brawler's Gloves (+DMG in Pos 1) is completely dead in Pos 2.",
    "pos_1_flagellant": "Severe Conflict: Resurrection's Collar (+33% Heal, -15% Bleed) and Punishment's Hood (+20% Bleed, -20% Heal) cancel each other out with net stat loss.",
    "subscore": 0.2
  },
  "sustain_and_recovery": {
    "hp_sustain": "Functional via Flagellant Redeem/Exsanguinate and Occultist Wyrd Reconstruction.",
    "stress_sustain": "Houndmaster Cry Havoc provides AoE stress relief.",
    "subscore": 1.4
  },
  "final_score": 6.4
}

```

---

#### Example 3: The Frontline Lockout (Hard Failure / Low Tier)

**Input Party:**

* **Pos 4: Flagellant** | Skills: `[Punish, Rain of Sorrows, Exsanguinate, Redeem]` | Trinkets: `[Punishment's Hood, Heartburst Hood]`
* **Pos 3: Crusader** | Skills: `[Smite, Zealous Accusation, Stunning Blow, Bulwark of Faith]` | Trinkets: `[Defender's Seal, Swordsman's Crest]`
* **Pos 2: Grave Robber** | Skills: `[Pick to the Face, Shadow Fade, Poison Dart, Toxin Trickery]` | Trinkets: `[Sickening Satchel, Quickening Satchel]`
* **Pos 1: Occultist** | Skills: `[Abyssal Artillery, Vulnerability Hex, Weakening Curse, Sacrificial Stab]` | Trinkets: `[Archer's Ring, Eldritch Killing Incense]`

**Evaluation Output:**

```json
{
  "positional_legality": {
    "pos_4_flagellant": "Invalid (Punish, Rain of Sorrows, Exsanguinate require Pos 1-2. Redeem requires <40% HP. Turn 1 dead hero).",
    "pos_3_crusader": "Invalid (Smite, Zealous Accusation, Stunning Blow, Bulwark of Faith require Pos 1-2. No Holy Lance equipped).",
    "pos_2_grave_robber": "Valid (Pick, Shadow Fade, Poison Dart, Toxin Trickery usable from Pos 2).",
    "pos_1_occultist": "Invalid (Abyssal Artillery requires Pos 3-4. Fragile 19 HP hero placed in frontline).",
    "subscore": 0.75
  },
  "synergy_and_mechanics": {
    "speed_tiers": "Broken. Ranks 3 and 4 are completely unable to take offensive or utility actions on Round 1 without passing/moving.",
    "damage_combos": "Zero synergy. Flagellant and Crusader cannot attack. GR has no Blight setup from allies to leverage Sickening Satchel.",
    "crowd_control": "Zero usable stuns (Crusader Stunning Blow locked).",
    "subscore": 0.3
  },
  "trinket_compatibility": {
    "pos_4_flagellant": "Wasted: Punishment's Hood boosts Bleed skills that cannot be cast.",
    "pos_3_crusader": "Wasted: Swordsman's Crest (-50% Heal, +10% Melee DMG) on melee skills that cannot be cast.",
    "pos_2_grave_robber": "Suboptimal: Quickening Satchel gives flat SPD, but Sickening Satchel has no team Blight synergy.",
    "pos_1_occultist": "Severe Conflict: Archer's Ring (+Ranged ACC) equipped while Abyssal Artillery is locked out in Pos 1.",
    "subscore": 0.2
  },
  "sustain_and_recovery": {
    "hp_sustain": "Zero reliable active healing (Occultist Wyrd unequipped; Crusader Battle Heal unequipped; Flagellant heal locked).",
    "stress_sustain": "Zero stress recovery (Crusader Inspiring Cry unequipped; Flagellant Endure unequipped).",
    "subscore": 0.0
  },
  "final_score": 1.25
}

```