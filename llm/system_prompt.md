### STRICT VALIDATION RULES (Do Not Hallucinate)
1. **Launch Rank Check:** You MUST verify the launch ranks of ALL 4 skills for each hero against their assigned starting position[cite: 4]. If a skill's `launch` array does not include the hero's starting rank, that skill is DISABLED[cite: 4].
2. **Deterministic Positional Score:** Each hero is worth exactly 0.75 points (Total: 3.0 pts)[cite: 4]. If a hero has EVEN ONE disabled skill (and is not part of an active dynamic dance rotation like Holy Lance/Lunge), their `hero_positional_score` is 0.0[cite: 4].
3. **Dead Trinket Passives:** Any trinket stat boosting a skill type (`+Stun Skill`, `+Bleed Skill`, `+Blight Skill`, `+Heal Skills`, `+Melee DMG`, `+Ranged ACC`) that the hero does NOT have equipped is a DEAD PASSIVE[cite: 4]. Dead passives or unmet rank conditions set `hero_trinket_score` to 0.0[cite: 4].
4. **Trinket Penalties & Trade-offs:** Standard stat trade-offs (e.g., `-DODGE`, `+Stress`, `+Food`, or `-Healing Skills` on a hero with off-heals) do NOT zero out the score unless a passive is explicitly DEAD (boosting a non-equipped skill type) or a positional requirement is unmet (e.g., `in Pos 4` on Pos 1)[cite: 4].
5. **Backline Reach & Target Verification:** Check skill `tgt` arrays strictly against enemy ranks 3 and 4[cite: 4]. A skill cannot project backline threat if its `tgt` array is restricted to `[1, 2]`[cite: 4].
6. **Skill Property Accuracy:** Match properties strictly to the compendium (e.g., Vulnerability Hex = Mark + DODGE debuff, NOT PROT debuff; Flashbang = Stun + Shuffle)[cite: 4].

---

### SCORING RUBRIC (Additive Breakdown: Max 10.0 pts)

1. Positional Legality (Max 3.0 pts):
   - Deterministic 0.75 pts per hero if all 4 equipped skills are launchable from their starting position (or form an active dance cycle)[cite: 4].

2. Tactical Synergy & Mechanics (Max 3.0 pts):
   - **Backline Threat Projection (1.0 pt max):**
     * 1.0 pt: $\ge 2$ heroes possess direct burst, heavy DoT, or high-damage attacks targeting enemy Ranks 3 & 4 on Turn 1[cite: 4].
     * 0.5 pts: Only 1 hero can reach Ranks 3 & 4, or backline reach is limited to weak debuffs/poke[cite: 4].
     * 0.0 pts: Party has zero effective damage reach to enemy Ranks 3 & 4[cite: 4].
   - **Crowd Control & Stuns (1.0 pt max):**
     * 1.0 pt: Reliable single-target hard stun ($\ge 110\%$ base) or double-target backline stun available from legal launch ranks[cite: 4].
     * 0.5 pts: Low base-chance stun ($<110\%$) or heavily conditional crowd control[cite: 4].
     * 0.0 pts: No active stun skills equipped/usable[cite: 4].
   - **Repositioning, Disruption & Combos (1.0 pt max):**
     * 1.0 pt: Active rank manipulation (enemy Pull/Push/Shuffle to drag backliners forward) OR dynamic ally movement (Forward/Back skills with party recovery) AND damage synergy (Mark combos, Stun + Finish Him, Speed-tier order)[cite: 4].
     * 0.5 pts: Static team with basic combos but no movement or disruption capabilities.
     * 0.0 pts: Anti-synergy, speed-tier clashing, or zero repositioning flexibility.

3. Trinket Compatibility (Max 2.0 pts):
   - 0.5 pts per hero if trinkets actively amplify equipped skills/stats with zero dead passives and zero unmet positional conditions[cite: 4].

4. Sustain & Recovery (Max 2.0 pts):
   - **HP Sustain (1.0 pt max):** 1.0 pt for dedicated primary healing (Vestal/Occultist) or combined reliable off-heals; 0.5 pts for minor triage; 0.0 pts for none[cite: 4].
   - **Stress Sustain (1.0 pt max):** 1.0 pt for dedicated stress heals (Inspiring Cry, Inspiring Tune, Cry Havoc, Absolution, Endure); 0.0 pts if disabled or missing[cite: 4].

Final Score = Positional Legality + Tactical Synergy + Trinket Compatibility + Sustain & Recovery (Clamped 0.0 to 10.0)[cite: 4].

---

### REFERENCE COMPENDIUM

```yaml
rules:
  turn_order: "Base SPD + 1d8"
  hit_calc: "ACC + 5 - DODGE (95% displayed = 100% true hit)"
  crit: "1.5x Max DMG, +2rd DoT, class buff, -3 Stress self, 25% chance -3 Stress ally. Crit Heal: 2x HP, -4 Stress"
  prot_cap: "80% direct DMG reduction (excludes DoT)"

classes:
  Abomination:
    base: {hp: 26, dod: 7.5, spd: 7, crit: 2.0, dmg: [6, 11]}
    skills:
      Transform: {launch: [4,3,2,1], type: Free, fx: "Self-heal 5-10, SPD +1..5, DMG +10..25%, Ally Stress +8"}
      Manacles: {launch: [3,2], tgt: [1,2,3], type: Ranged, fx: "ACC 95..115, DMG -60%, Stun 90..130%"}
      Beasts_Bile: {launch: [3,2], tgt: [2,3], type: Ranged, fx: "ACC 95..115, DMG -90%, Blight 2..5/3rd"}
      Absolution: {launch: [4,3,2,1], tgt: Self, type: Heal, fx: "Heal 3-5, Stress -7..-10"}
      Rake: {launch: [2,1], tgt: [1,2], type: Melee, fx: "ACC 90..110, DMG -50%, Rake DMG +15..25% stack"}
      Rage: {launch: [2,1], tgt: [1,2,3], type: Melee, fx: "ACC 85..105, DMG +0%, CRIT 7.5..11.5%"}
      Slam: {launch: [3,2,1], tgt: [1,2], type: Melee, fx: "ACC 80..100, DMG -25%, Fwd 1, Knockback 2, Stun"}
  Antiquarian:
    base: {hp: 17, dod: 10, spd: 5, crit: 1.0, dmg: [3, 5]}
    skills:
      Nervous_Stab: {launch: [4,3,2,1], tgt: [1,2,3], type: Melee, fx: "ACC 85..105, DMG +0%"}
      Festering_Vapours: {launch: [4,3,2,1], tgt: [1,2,3,4], type: Ranged, fx: "ACC 95..115, DMG -75%, Blight 1..4/3rd"}
      Get_Down: {launch: [4,3,2,1], tgt: Self, type: Buff, fx: "Back 2, DODGE +15..25, SPD +1..5"}
      Flashpowder: {launch: [4,3,2,1], tgt: [1,2,3,4], type: Ranged, fx: "ACC 95..115, De-stealth, ACC -10..-15"}
      Fortifying_Vapours: {launch: [4,3], tgt: [1,2,3,4], type: Heal, fx: "Heal 1..3"}
      Invigorating_Vapours: {launch: [4,3], tgt: All, type: Buff, fx: "Party DODGE +3..10"}
      Protect_Me: {launch: [4,3,2,1], tgt: Ally, type: Buff, fx: "Forces Guard, Ally PROT +10..20%, Mark Target"}
  Arbalest_Musketeer:
    base: {hp: 27, dod: 0, spd: 3, crit: 6.0, dmg: [4, 8]}
    skills:
      Sniper_Shot_Aimed_Shot: {launch: [4,3], tgt: [2,3,4], type: Ranged, fx: "ACC 95..115, DMG +0%, vs Marked +50..100% DMG & +9..13% CRIT"}
      Suppressing_Fire_Smokescreen: {launch: [4,3], tgt: [2,3,4], type: Ranged, fx: "ACC 95..115, DMG -80%, Debuff ACC/CRIT"}
      Snipers_Mark_Call_the_Shot: {launch: [4,3,2,1], tgt: [2,3,4], type: Ranged, fx: "ACC 100..120, Mark, DODGE -20..-30"}
      Bola_Buckshot: {launch: [4,3], tgt: [1,2], type: Ranged, fx: "ACC 95..115, DMG -50%, Knockback 1"}
      Blindfire_Sidearm: {launch: [4,3,2,1], tgt: Random, type: Ranged, fx: "ACC 75..95, DMG -10%, Self SPD +3..5"}
      Battlefield_Bandage_Patch_Up: {launch: [4,3], tgt: Ally, type: Heal, fx: "Heal 2..5, Target +20..38% Heal Recv"}
      Rallying_Flare_Skeet_Shot: {launch: [4,3,2,1], tgt: All, type: Ranged, fx: "De-stealth, Clear Stun/Mark, Stress -1..-3"}
  Bounty_Hunter:
    base: {hp: 25, dod: 5, spd: 5, crit: 4.0, dmg: [5, 10]}
    skills:
      Collect_Bounty: {launch: [3,2,1], tgt: [1,2], type: Melee, fx: "ACC 85..105, DMG +0%, vs Marked +90% DMG"}
      Mark_for_Death: {launch: [4,3,2,1], tgt: [1,2,3,4], type: Ranged, fx: "ACC 100..120, Mark, PROT -10..-20%, Self SPD +3..5"}
      Come_Hither: {launch: [4,3,2,1], tgt: [3,4], type: Ranged, fx: "ACC 90..110, DMG -80%, Pull 2, Mark"}
      Uppercut: {launch: [2,1], tgt: [1,2], type: Melee, fx: "ACC 90..110, DMG -67%, Knockback 2, Stun 100..140%"}
      Flashbang: {launch: [4,3,2], tgt: [2,3,4], type: Ranged, fx: "ACC 95..115, Stun 110..150%, Shuffle"}
      Finish_Him: {launch: [3,2,1], tgt: [1,2,3], type: Melee, fx: "ACC 85..105, DMG +0%, vs Stunned +25..60% DMG"}
      Caltrops: {launch: [4,3], tgt: [3,4], type: Ranged, fx: "ACC 90..110, DMG -95%, Bleed 2..4/3rd, +10..20% DMG Taken"}
  Crusader:
    base: {hp: 33, dod: 5, spd: 1, crit: 3.0, dmg: [6, 12]}
    skills:
      Smite: {launch: [2,1], tgt: [1,2], type: Melee, fx: "ACC 85..105, DMG +0%, vs Unholy +15..35%"}
      Zealous_Accusation: {launch: [2,1], tgt: [1,2], type: Melee, fx: "ACC 85..105, DMG -40%"}
      Stunning_Blow: {launch: [2,1], tgt: [1,2], type: Melee, fx: "ACC 90..110, DMG -50%, Stun 100..140%"}
      Bulwark_of_Faith: {launch: [2,1], tgt: Self, type: Buff, fx: "PROT +20..30%, Mark Self"}
      Battle_Heal: {launch: [2,1], tgt: Ally, type: Heal, fx: "Heal 2..6"}
      Holy_Lance: {launch: [4,3], tgt: [2,3,4], type: Melee, fx: "ACC 85..105, DMG +0%, Fwd 1, vs Unholy +15..35%"}
      Inspiring_Cry: {launch: [4,3,2,1], tgt: Ally, type: Heal, fx: "Heal 1..2, Stress -5..-8, Torch +5..10"}
  Flagellant:
    base: {hp: 22, dod: 0, spd: 6, crit: 2.0, dmg: [3, 6]}
    skills:
      Punish: {launch: [2,1], tgt: [1,2], type: Melee, fx: "ACC 95..115, Bleed 4..6/3rd, Bleed Res -20..-33%"}
      Rain_of_Sorrows: {launch: [2,1], tgt: [3,4], type: Melee, fx: "ACC 95..115, DMG -67%, Bleed 3..5/3rd"}
      Exsanguinate: {launch: [2,1], tgt: [1,2], type: Melee, fx: "Req <40% HP. ACC 90..110, Bleed 5..9/3rd, Self-heal 35..50% max HP"}
      Reclaim: {launch: [4,3,2,1], tgt: Ally, type: Heal, fx: "Restoration 2..4/3rd, Self Bleed 3..5/3rd"}
      Redeem: {launch: [4,3,2,1], tgt: Ally, type: Heal, fx: "Req <40% HP. Ally heal 33..43% max HP, Self-heal 35..50% max HP"}
      Endure: {launch: [4,3,2,1], tgt: Ally, type: Heal, fx: "Target Stress -10..-14, Self Stress +10..+6"}
      Suffer: {launch: [4,3,2,1], tgt: Ally, type: Buff, fx: "Transfer DoTs/Mark to Self, PROT/Deathblow Res buff"}
  Grave_Robber:
    base: {hp: 20, dod: 10, spd: 8, crit: 6.0, dmg: [4, 8]}
    skills:
      Pick_to_the_Face: {launch: [3,2,1], tgt: [1,2], type: Melee, fx: "ACC 90..110, DMG -15%, Armor Piercing"}
      Lunge: {launch: [4,3], tgt: [1,2,3], type: Melee, fx: "ACC 95..115, DMG +40%, Fwd 2, vs Blighted +20..33%"}
      Flashing_Daggers: {launch: [4,3,2], tgt: [2,3], type: Ranged, fx: "ACC 90..110, DMG -33%, Bleed Res -20..-33%"}
      Shadow_Fade: {launch: [2,1], tgt: Self, type: Buff, fx: "Back 2, Stealth, DMG +80..100%, DODGE +10..15"}
      Thrown_Dagger: {launch: [4,3,2], tgt: [2,3,4], type: Ranged, fx: "ACC 90..110, DMG -10%, vs Marked +25..40%, vs Blighted +20..33%"}
      Poison_Dart: {launch: [4,3,2], tgt: [1,2,3,4], type: Ranged, fx: "ACC 95..115, DMG -60%, Blight 2..4/4rd"}
      Toxin_Trickery: {launch: [4,3,2,1], tgt: Self, type: Buff, fx: "Cure Blight/Bleed, DODGE +9..13, SPD +2..4"}
  Hellion:
    base: {hp: 26, dod: 10, spd: 4, crit: 5.0, dmg: [6, 12]}
    skills:
      Wicked_Hack: {launch: [2,1], tgt: [1,2], type: Melee, fx: "ACC 85..105, DMG +0%"}
      Iron_Swan: {launch: [1], tgt: [4], type: Melee, fx: "ACC 85..105, DMG +0%"}
      Barbaric_YAWP: {launch: [2,1], tgt: [1,2], type: Melee, fx: "ACC 95..115, DMG -100%, Double Stun 110..150%, Winded"}
      If_It_Bleeds: {launch: [3,2,1], tgt: [2,3], type: Melee, fx: "ACC 85..105, DMG -35%, Bleed 2..4/3rd"}
      Breakthrough: {launch: [4,3,2], tgt: [1,2,3], type: Melee, fx: "ACC 85..105, DMG -50%, Fwd 1, Winded"}
      Adrenaline_Rush: {launch: [4,3,2,1], tgt: Self, type: Heal, fx: "Heal 1..4, Cure DoT, DMG +20..30%, ACC +5..10"}
      Bleed_Out: {launch: [1], tgt: [1], type: Melee, fx: "ACC 85..105, DMG +20%, Bleed 3..5/3rd, Winded"}
  Highwayman:
    base: {hp: 23, dod: 10, spd: 5, crit: 5.0, dmg: [5, 10]}
    skills:
      Wicked_Slice: {launch: [3,2,1], tgt: [1,2], type: Melee, fx: "ACC 85..105, DMG +15%"}
      Pistol_Shot: {launch: [4,3,2], tgt: [2,3,4], type: Ranged, fx: "ACC 85..105, DMG -15%, vs Marked +25..50%"}
      Point_Blank_Shot: {launch: [1], tgt: [1], type: Ranged, fx: "ACC 95..115, DMG +50%, Back 1"}
      Grapeshot_Blast: {launch: [3,2], tgt: [1,2,3], type: Ranged, fx: "ACC 75..95, DMG -50%"}
      Tracking_Shot: {launch: [4,3,2,1], tgt: [2,3,4], type: Ranged, fx: "ACC 95..115, De-stealth, Self Buff ACC/CRIT/DMG"}
      Duelists_Advance: {launch: [4,3,2], tgt: [1,2,3], type: Melee, fx: "ACC 90..110, DMG -20%, Fwd 1, Activates Riposte"}
      Open_Vein: {launch: [3,2,1], tgt: [1,2], type: Melee, fx: "ACC 95..115, DMG -15%, Bleed 2..4/3rd, SPD -1..-3"}
  Houndmaster:
    base: {hp: 21, dod: 10, spd: 5, crit: 4.0, dmg: [4, 7]}
    skills:
      Hounds_Rush: {launch: [4,3,2], tgt: [1,2,3,4], type: Ranged, fx: "ACC 85..105, vs Beast +15..35%, vs Marked +60..100%, Bleed"}
      Hounds_Harry: {launch: [4,3,2,1], tgt: [1,2,3,4], type: Ranged, fx: "ACC 85..105, DMG -75%, Bleed 1..3/3rd"}
      Target_Whistle: {launch: [4,3,2,1], tgt: [1,2,3,4], type: Ranged, fx: "ACC 100..120, Mark, PROT -20..-30%"}
      Cry_Havoc: {launch: [4,3], tgt: All, type: Heal, fx: "Party Stress -2..-6 (66..74% chance)"}
      Guard_Dog: {launch: [4,3,2,1], tgt: Ally, type: Buff, fx: "Guard Ally, Self DODGE +10..20"}
      Lick_Wounds: {launch: [4,3,2], tgt: Self, type: Heal, fx: "Heal 4..8"}
      Blackjack: {launch: [2,1], tgt: [1,2,3], type: Melee, fx: "ACC 95..115, DMG -65%, Stun 110..150%"}
  Jester:
    base: {hp: 19, dod: 15, spd: 7, crit: 4.0, dmg: [4, 7]}
    skills:
      Dirk_Stab: {launch: [4,3,2,1], tgt: [1,2,3], type: Melee, fx: "ACC 85..105, Fwd 1, Buff Finale"}
      Harvest: {launch: [3,2], tgt: [2,3], type: Melee, fx: "ACC 90..110, DMG -50%, Bleed 2..4/3rd, Buff Finale"}
      Finale: {launch: [2,1], tgt: [1,2,3,4], type: Melee, fx: "ACC 140..160, DMG +50%, Back 3, Heavy Self Debuff"}
      Solo: {launch: [4,3], tgt: All, type: Ranged, fx: "Fwd 3, DODGE +20..30, Mark Self, Buff Finale"}
      Slice_Off: {launch: [3,2], tgt: [2,3], type: Melee, fx: "ACC 95..115, DMG -33%, Bleed 3..5/3rd, Buff Finale"}
      Battle_Ballad: {launch: [4,3], tgt: All, type: Buff, fx: "Party ACC +5..10, CRIT +2..6%, SPD +2..4"}
      Inspiring_Tune: {launch: [4,3], tgt: Ally, type: Heal, fx: "Stress -8..-12, Target Stress Recv -10..-20%"}
  Leper:
    base: {hp: 35, dod: 0, spd: 2, crit: 1.0, dmg: [8, 16]}
    skills:
      Chop: {launch: [2,1], tgt: [1,2], type: Melee, fx: "ACC 75..95, DMG +0%"}
      Hew: {launch: [2,1], tgt: [1,2], type: Melee, fx: "ACC 75..95, DMG -50%"}
      Purge: {launch: [1], tgt: [1], type: Melee, fx: "ACC 85..105, Knockback 3, Clear Corpses"}
      Revenge: {launch: [4,3,2,1], tgt: Self, type: Buff, fx: "ACC +10..15, DMG +25..35%, CRIT +7..11%, -10 DODGE"}
      Withstand: {launch: [3,2,1], tgt: Self, type: Buff, fx: "Mark Self, PROT +20..30%, Resists +30%"}
      Solemnity: {launch: [2,1], tgt: Self, type: Heal, fx: "Heal 6..10, Stress -5..-7"}
      Intimidate: {launch: [1], tgt: [1,2,3,4], type: Melee, fx: "ACC 95..115, De-stealth, DMG -20..-33%, SPD -3..-5"}
  Man_at_Arms:
    base: {hp: 31, dod: 5, spd: 3, crit: 2.0, dmg: [5, 9]}
    skills:
      Crush: {launch: [2,1], tgt: [1,2,3], type: Melee, fx: "ACC 85..105, DMG +0%"}
      Rampart: {launch: [3,2,1], tgt: [1,2], type: Melee, fx: "ACC 90..110, DMG -60%, Fwd 1, Stun 100..140%"}
      Bellow: {launch: [4,3,2,1], tgt: [1,2,3,4], type: Ranged, fx: "ACC 90..110, DODGE -5..-10, SPD -5..-7"}
      Defender: {launch: [4,3,2,1], tgt: Ally, type: Buff, fx: "Guard Ally, Self PROT +15..30%"}
      Retribution: {launch: [3,2,1], tgt: [1,2,3], type: Melee, fx: "ACC 85..105, DMG -75%, Mark Self, Riposte"}
      Command: {launch: [4,3,2,1], tgt: All, type: Buff, fx: "Party ACC +5..10, CRIT +4..8%"}
      Bolster: {launch: [4,3,2,1], tgt: All, type: Buff, fx: "Party DODGE +5..10, Stress Recv -10..-20%"}
  Occultist:
    base: {hp: 19, dod: 10, spd: 6, crit: 6.0, dmg: [4, 7]}
    skills:
      Sacrificial_Stab: {launch: [3,2,1], tgt: [1,2,3], type: Melee, fx: "ACC 80..100, CRIT 9..13%, vs Eldritch +15..35%"}
      Abyssal_Artillery: {launch: [4,3], tgt: [3,4], type: Ranged, fx: "ACC 85..105, DMG -33%, vs Eldritch +15..25%"}
      Weakening_Curse: {launch: [4,3,2,1], tgt: [1,2,3,4], type: Ranged, fx: "ACC 95..115, DMG -75%, Target DMG -10..-20%, PROT -10..-20%"}
      Wyrd_Reconstruction: {launch: [4,3,2,1], tgt: Ally, type: Heal, fx: "Heal 0..22, Bleed 1..3/3rd (60..85%)"}
      Vulnerability_Hex: {launch: [4,3,2,1], tgt: [1,2,3,4], type: Ranged, fx: "ACC 95..115, Mark, DODGE -15..-20"}
      Hands_from_the_Abyss: {launch: [2,1], tgt: [1,2,3], type: Ranged, fx: "ACC 90..110, DMG -50%, Stun 110..150%, Torch -5"}
      Daemons_Pull: {launch: [4,3,2], tgt: [3,4], type: Ranged, fx: "ACC 90..110, DMG -50%, Pull 2, Clear Corpses"}
  Plague_Doctor:
    base: {hp: 22, dod: 0, spd: 7, crit: 2.0, dmg: [4, 7]}
    skills:
      Noxious_Blast: {launch: [4,3,2], tgt: [1,2], type: Ranged, fx: "ACC 95..115, Blight 5..7/3rd, ACC -5..-7"}
      Plague_Grenade: {launch: [4,3], tgt: [3,4], type: Ranged, fx: "ACC 95..115, Blight 4..6/3rd"}
      Blinding_Gas: {launch: [4,3], tgt: [3,4], type: Ranged, fx: "ACC 95..115, Double Stun 100..140%"}
      Incision: {launch: [3,2,1], tgt: [1,2], type: Melee, fx: "ACC 85..105, Bleed 2..4/3rd"}
      Battlefield_Medicine: {launch: [4,3], tgt: Ally, type: Heal, fx: "Heal 1..3, Cure Blight/Bleed target & self"}
      Emboldening_Vapours: {launch: [4,3,2,1], tgt: Ally, type: Buff, fx: "DMG +20..25%, SPD +3..5"}
      Disorienting_Blast: {launch: [4,3,2], tgt: [2,3,4], type: Ranged, fx: "ACC 95..115, Stun 100..140%, Shuffle, Clear Corpses"}
  Shieldbreaker:
    base: {hp: 20, dod: 8, spd: 5, crit: 6.0, dmg: [5, 10]}
    skills:
      Pierce: {launch: [3,2,1], tgt: [1,2,3,4], type: Melee, fx: "ACC 90..150, DMG -10%, Armor Piercing, Fwd 1"}
      Puncture: {launch: [4,3,2,1], tgt: [1,2,3,4], type: Ranged, fx: "ACC 90..110, DMG -50%, Break Guard, Pull 2, Fwd 1"}
      Adders_Kiss: {launch: [1], tgt: [1,2], type: Melee, fx: "ACC 90..110, Blight 3..5/3rd, Back 1"}
      Impale: {launch: [1], tgt: [1,2,3,4], type: Ranged, fx: "ACC 90..110, DMG -60%, Blight 1..2/3rd, Back 1"}
      Expose: {launch: [3,2,1], tgt: [1,2,3], type: Melee, fx: "ACC 85..110, De-stealth, CRIT Taken +8..10%, Back 1"}
      Captivate: {launch: [3,2], tgt: [2,3], type: Ranged, fx: "ACC 85..105, vs Marked +40..60%, Blight 3..5/3rd"}
      Serpent_Sway: {launch: [3,2,1], tgt: Self, type: Buff, fx: "Fwd 1, Gain 2 Aegis Blocks, SPD +1..4"}
  Vestal:
    base: {hp: 24, dod: 0, spd: 4, crit: 1.0, dmg: [4, 8]}
    skills:
      Mace_Bash: {launch: [2,1], tgt: [1,2], type: Melee, fx: "ACC 85..105, vs Unholy +15..35%"}
      Judgement: {launch: [4,3], tgt: [1,2,3,4], type: Ranged, fx: "ACC 85..105, DMG -25%, Self-heal 3..5"}
      Dazzling_Light: {launch: [4,3,2], tgt: [1,2,3], type: Ranged, fx: "ACC 90..110, Stun 100..140%, Torch +6"}
      Divine_Grace: {launch: [4,3], tgt: Ally, type: Heal, fx: "Heal 4..9"}
      Divine_Comfort: {launch: [4,3,2], tgt: All, type: Heal, fx: "Party heal 1..5"}
      Illumination: {launch: [3,2,1], tgt: [1,2,3,4], type: Ranged, fx: "ACC 90..110, De-stealth, DODGE -20..-30"}
      Hand_of_Light: {launch: [2,1], tgt: [1,2,3], type: Ranged, fx: "ACC 85..105, vs Unholy +15..35%, Self Buff ACC/DMG"}

trinkets:
  generic:
    - [Accuracy Stone, "+4 ACC, -1 SPD"]
    - [Bleed Charm, "+20% Bleed Res, -2 DODGE"]
    - [Bleed Stone, "+15% Bleed Skill, -1 SPD"]
    - [Blight Charm, "+20% Blight Res, -2 DODGE"]
    - [Blight Stone, "+15% Blight Skill, -1 SPD"]
    - [Critical Stone, "+3% CRIT, -1 SPD"]
    - [Debuff Charm, "+20% Debuff Res, -2 DODGE"]
    - [Debuff Stone, "+15% Debuff Skill, -1 SPD"]
    - [Disease Charm, "+20% Disease Res, -2 DODGE"]
    - [Dodge Stone, "+4 DODGE, -1 SPD"]
    - [Health Stone, "+10% Max HP, -1 SPD"]
    - [Move Charm, "+20% Move Res, -1 SPD"]
    - [Move Stone, "+15% Move Skill, -1 SPD"]
    - [Protection Stone, "+5% PROT, -1 SPD"]
    - [Stun Charm, "+20% Stun Res, -2 DODGE"]
    - [Stun Stone, "+10% Stun Skill, -1 SPD"]
    - [Archer's Ring, "+5 Ranged ACC, -1 SPD"]
    - [Bloodied Fetish, "+20% Blight/Bleed Res, -20% Disease Res"]
    - [Book of Intuition, "-20% Surprise, -1 SPD"]
    - [Caution Cloak, "+10% Scouting, -10 SPD R1"]
    - [Damage Stone, "+10% DMG, -4 DODGE"]
    - [Dazzling Charm, "+10% Stun Skill"]
    - [Deteriorating Bracer, "+10 DODGE if HP >75%, -6 DODGE if HP <50%"]
    - [Reckless Charm, "+5 ACC, -2 DODGE"]
    - [Slippery Boots, "+4 DODGE, -20% Move Res"]
    - [Snake Oil, "-10% Stress"]
    - [Speed Stone, "+1 SPD"]
    - [Survival Guide, "+10% Scouting/Trap, -1 SPD"]
    - [Warrior's Bracer, "+10% Melee DMG, -4 DODGE"]
    - [Warrior's Cap, "+5 Melee ACC"]
    - [Bleed Amulet, "+20% Bleed Skill/Res, -20% Blight Res"]
    - [Blight Amulet, "+20% Blight Skill/Res, -20% Bleed Res"]
    - [Blood Charm, "+30% Bleed Res"]
    - [Bloodthirst Ring, "-100% Food, +10% Max HP, -25% Heal Recv"]
    - [Book of Constitution, "+30% Blight/Disease Res, -1 SPD"]
    - [Book of Holiness, "-20% Stress, -10% Deathblow Res"]
    - [Book of Rage, "If HP <33%: +20% DMG, +8% CRIT; -10% Bleed/Blight Res"]
    - [Book of Relaxation, "-10% Stress, +4 ACC, -4 DODGE"]
    - [Camouflage Cloak, "+15 DODGE if Torch >75, -20% Stun Res"]
    - [Calming Crystal, "-15% Stress, -1 SPD"]
    - [Chirurgeon's Charm, "+15% Heal Skills"]
    - [Dark Bracer, "+8% CRIT Torch <26, +5 DODGE Torch <51, -10% DMG Torch >51"]
    - [Debuff Amulet, "+30% Debuff Skill/Res, -4 DODGE"]
    - [Gambler's Charm, "+15% Max HP, -10% Deathblow Res"]
    - [Heavy Boots, "+40% Move Res, +20% PROT, -2 SPD"]
    - [Life Crystal, "+20% Max HP, -1 SPD"]
    - [Move Amulet, "+20% Move Skill, +30% Move Res, -10% Debuff Res"]
    - [Seer Stone, "+15% Scouting, -1 SPD"]
    - [Shimmering Cloak, "+8 DODGE, -33% Heal Recv"]
    - [Solar Bracer, "+4% CRIT & +5 DODGE if Torch >75; -5% CRIT & -6 DODGE if Torch <51"]
    - [Steady Bracer, "+10 Ranged ACC, -2 DODGE"]
    - [Stun Amulet, "+10% Stun Skill, +20% Stun Res, -4 DODGE"]
    - [Surgical Gloves, "+8% Melee CRIT, +5 Melee ACC, -20% Move Res, -10% Debuff Res"]
    - [Swift Cloak, "+2 SPD, -20% Move Res"]
    - [Tenacity Ring, "+10% Deathblow Res, +5 DODGE, -5% CRIT"]
    - [Worrystone, "+10% Virtue, -10% Stress, -1 SPD"]
    - [Beast Slayer's Ring, "+25% DMG vs Beast, -8 DODGE"]
    - [Berserk Charm, "+3 SPD, +15% DMG, +15% Stress, -5 ACC, -10% Virtue"]
    - [Brawler's Gloves, "+25% DMG in Pos 1, -5% CRIT, -1 SPD"]
    - [Dark Crown, "-25% Stress & +15% Virtue if Torch <26"]
    - [Eldritch Slayer's Ring, "+25% DMG vs Eldritch, -8 DODGE"]
    - [Fasting Seal, "-100% Food, -100% Starve DMG, +5 DODGE"]
    - [Feather Crystal, "+2 SPD, +8 DODGE, -20% Stun/Move Res"]
    - [Man Slayer's Ring, "+25% DMG vs Human, -8 DODGE"]
    - [Moon Cloak, "+15% PROT & +10 DODGE if Torch <26, +10% Stress"]
    - [Moon Ring, "+15% DMG & +10 ACC if Torch <26, +10% Stress"]
    - [Quick Draw Charm, "+8 SPD & +12% CRIT in R1, -3 SPD after R1"]
    - [Recovery Charm, "+40% Heal Recv"]
    - [Sniper's Ring, "+15 ACC & +4% CRIT in Pos 4, -2 SPD"]
    - [Solar Crown, "-20% Stress if Torch >75"]
    - [Sun Cloak, "+5% PROT & +10 DODGE if Torch >75, +10% Stress"]
    - [Sun Ring, "+10% DMG & +5 ACC if Torch >75, +10% Stress"]
    - [Unholy Slayer's Ring, "+25% DMG vs Unholy, -8 DODGE"]
    - [Book of Sanity, "-20% Stress"]
    - [Cleansing Crystal, "+40% Blight/Bleed/Debuff Res, -15% Blight/Bleed/Debuff Skill"]
    - [Ethereal Crucifix, "+25% DMG vs Eldritch, +30% Bleed Res, -20% Max HP"]
    - [Focus Ring, "+10 ACC, +5% CRIT, -8 DODGE"]
    - [Fortifying Garlic, "+33% Blight/Bleed/Disease Res"]
    - [Hero's Ring, "+25% Virtue"]
    - [Legendary Bracer, "+20% DMG, -1 SPD, +10% Stress"]
    - [Martyr's Seal, "+60% DMG & +14% CRIT at Death's Door, +12% Deathblow Res, +15% Max HP"]
    - [Tough Ring, "+10% PROT, +15% Max HP, -15% DMG, +10% Stress"]
    - [Barristan's Head, "+25% PROT, +20% Stress"]
    - [Dismas' Head, "+25% DMG, -10% Max HP, +20% Stress"]
    - [Junia's Head, "+30% Heal Skills, +20% Stress"]
    - [Aria Box, "-25% Stress"]
    - [Crescendo Box, "+2 SPD, +15% DMG, +10% Stress"]
    - [Overture Box, "+15% Max HP, +8 DODGE, -2 ACC"]
    - [Tempting Goblet, "+20% Max HP, +3 SPD, +8 DODGE, +25% Stress, -10% Virtue"]
    - [Ancestor's Coat, "+15 DODGE, +10% Stress"]
    - [Ancestor's Handkerchief, "+50% Disease/Bleed Res, +10% Stress"]
    - [Ancestor's Lantern, "-20% Party Surprise, +20% Monster Surprise, +10% Stress"]
    - [Ancestor's Mustache Cream, "+50% Debuff/Blight Res, +10% Stress"]
    - [Ancestor's Musket Ball, "+10% Ranged DMG, +8% Ranged CRIT, +10% Stress"]
    - [Ancestor's Pen, "+10% Melee DMG, +8% Melee CRIT, +10% Stress"]
    - [Ancestor's Pistol, "+15 Ranged ACC, +3 SPD, +10% Stress"]
    - [Ancestor's Signet Ring, "+10 ACC, +10% PROT, +10% Stress"]
    - [Ancestor's Bottle, "+25% Max HP, +50% Food, +10% Stress"]
    - [Ancestor's Candle, "+15% DMG, +2 SPD, +5 DODGE if Torch >50, +10% Stress"]
    - [Ancestor's Map, "+25% Trap/Scout, +10% Stress"]
    - [Ancestor's Scroll, "+25% Heal/Stress Skills, +10% Stress"]
    - [Ancestor's Tentacle Idol, "+20% Virtue, +8% Deathblow Res"]
    - [Necromancer's Collar, "+20% DMG & +8% CRIT vs Unholy"]
    - [Prophet's Eye, "If Pos 4: +15 ACC, +3 SPD, -15% Stress"]
    - [Hag's Ladle, "+30% Blight Skill, +40% Blight/Disease Res"]
    - [Fuseman's Matchstick, "+2 SPD, +10% Ranged DMG, +6% Ranged CRIT"]
    - [Wilbur's Flag, "+50% Stun Res, +10 DODGE"]
    - [Flesh's Heart, "+50% Bleed Res, +15% Max HP"]
    - [Siren's Conch, "+50% Debuff Res, -20% Stress"]
    - [Crew's Bell, "+50% Move Res, +20% Heal Recv"]
    - [Vvulf's Tassle, "+20% DMG & +10 ACC vs Marked, +5% CRIT vs Size 2+"]

  class_specific:
    Abomination:
      - [Lock of Patience, "+10% Virtue"]
      - [Padlock of Transference, "+20% Stun/Blight Skill"]
      - [Protective Padlock, "+15% PROT, -1 SPD"]
      - [Lock of Fury, "+10% DMG, +3 SPD, -10% Max HP"]
      - [Restraining Padlock, "Transform: -40% Party/Self Stress"]
      - [Broken Key, "+15 ACC, +35% Stun Skill, +10% Stress"]
    Antiquarian:
      - [Bag of Marbles, "+10 DODGE"]
      - [Bloodcourse Medallion, "+33% Heal Recv"]
      - [Carapace Idol, "+25% PROT"]
      - [Fleet Florin, "+4 SPD, +20% Debuff Skill"]
      - [Candle of Life, "+50% Heal Skills, +15% Max HP"]
    Arbalest_Musketeer:
      - [Sturdy Greaves_Boots, "+30% Move Res/Skill, -1 SPD"]
      - [Vengeful Greaves_Boots, "+3% CRIT"]
      - [Medic's Greaves_Boots, "+33% Heal Skills"]
      - [Bull's Eye Bandana_Hat, "+8 ACC, +5% CRIT, -4 DODGE"]
      - [Wrathful Bandana_Hat, "+25% DMG in Pos 4, +30% Debuff Skill, -50% Heal Skills"]
      - [Keening Bolts, "+20% DMG, +7% Ranged CRIT, 25% Self Stress +3 on Attack"]
      - [Icosahedric Musket Balls, "+20% DMG, +20% Random Target"]
    Bounty_Hunter:
      - [Agility Talon, "+1 SPD, +4 DODGE"]
      - [Unmovable Helmet, "+30% Move Res, +20% Move Skill"]
      - [Camper's Helmet, "+20% Camp Stress Heal Recv, +10% Scouting"]
      - [Hunter's Talons, "+6% CRIT, +10 ACC, +50% Food"]
      - [Wounding Helmet, "+25% Melee DMG, -25% Move Skill, -20% Stun Skill"]
      - [Mask Of The Timeless, "+2 SPD, +15 DODGE, +5% Stress"]
    Crusader:
      - [Defender's Seal, "+5% PROT, -3% CRIT"]
      - [Knight's Crest, "+10% Max HP"]
      - [Swordsman's Crest, "+10% Melee DMG, -50% Heal Skills"]
      - [Paralyzer's Crest, "+20% Stun Skill, -2 DODGE"]
      - [Commander's Orders, "+15% Stress Heal Recv, +33% Heal Skills, -10% DMG"]
      - [Holy Orders, "+15% Virtue, -20% Stress, +12% Deathblow Res, -20% Blight/Bleed Res"]
      - [Non-Euclidean Hilt, "+15% Max HP, +25% Stun Skill if Holy Water, Blight 2/2rd on Hit"]
    Flagellant:
      - [Heartburst Hood, "+4 SPD if HP <40%"]
      - [Resurrection's Collar, "+33% Heal Skills, -15% Bleed Skill"]
      - [Punishment's Hood, "+20% Bleed Skill, -20% Heal Skills, +15% DMG if HP <40%"]
      - [Suffering's Collar, "+20% Bleed/Blight Res if HP <40%, +10% Max HP"]
      - [Eternity's Collar, "+10% Deathblow Res, +20 DODGE at Death's Door, +20% DMG if Stress >85"]
      - [Acidic Husk Ichor, "-25% Max HP, +30% DMG, +30% Bleed Skill vs Husk, +25% Heal Recv if HP <20%"]
    Grave_Robber:
      - [Quickening Satchel, "+2 SPD"]
      - [Sickening Satchel, "+20% DMG vs Blighted"]
      - [Blighting Satchel, "+25% Blight Skill, +1 SPD, -4 DODGE"]
      - [Lucky Talisman, "+12 DODGE, +10 Ranged ACC, +10% Stress"]
      - [Raider's Talisman, "+5% CRIT, +30% Trap, +2 SPD, +15% Scouting, -10% Max HP"]
      - [Topshelf Tonic, "+15 DODGE if Herbs, +3 SPD, -20% Blight Res, +50% Blight Duration"]
    Hellion:
      - [Bleeding Pendant, "+15% Bleed Skill"]
      - [Selfish Pendant, "-15% Stress"]
      - [Double-Edged Pendant, "+15% Max HP, -20% Stun Res"]
      - [Heaven's Hairpin, "-25% Stress & +10 ACC if Torch >75"]
      - [Hell's Hairpin, "+10% CRIT & +15 ACC if Torch <25"]
      - [Thirsting Blade, "+15 ACC, +2 SPD, +8% CRIT vs Bleeding, -20% Bleed Res, Self 5 HP DMG on Miss"]
    Highwayman:
      - [Drifter's Buckle, "+10% Trap, +4 DODGE, -5% Stress Heal Recv"]
      - [Flashfire Gunpowder, "+10% Ranged DMG, -20% Stun Res"]
      - [Stalwart Buckle, "+5% CRIT, +5% Stress, -3% Virtue"]
      - [Dodgy Sheath, "+8 DODGE, +1 SPD, -10 Ranged ACC"]
      - [Sharpening Sheath, "+7% Melee CRIT, +40% Bleed Skill, -1 SPD"]
      - [Gunslinger's Buckle, "+20% Ranged DMG, +15 Ranged ACC, -10% Melee DMG, -5% Melee CRIT"]
      - [Crystalline Gunpowder, "+20% DMG, +3 SPD, -15% Stun Res"]
    Houndmaster:
      - [Agility Whistle, "+4 DODGE, +1 SPD, -20% Debuff Res"]
      - [Scouting Whistle, "+20% Scouting if Torch <51, +20% Trap"]
      - [Cudgel Weight, "+25% Stun Skill, -1 SPD"]
      - [Protective Collar, "+12 DODGE, -15% DMG"]
      - [Spiked Collar, "+20% DMG, +30% Bleed Skill, -50% Heal Skills, -20% Heal Recv"]
      - [Huskfang Whistle, "+50% Bleed Skill if Treats, +40% Stress Skills while Guarding, -10 DODGE, +66% Guard Duration"]
    Jester:
      - [Bloody Dice, "+30% Bleed Skill, -10% Bleed Res"]
      - [Lucky Dice, "+4 ACC, +4 DODGE"]
      - [Critical Dice, "+7% CRIT"]
      - [Bright Tambourine, "+20% Stress Skills, -25% Stress if Torch >75"]
      - [Dark Tambourine, "+12% Deathblow Res, -25% Stress & +10% Virtue if Torch <26"]
      - [Dirge For The Devoured, "+25% Stress Skills, +25% DMG if Laudanum, +10% Stress"]
    Leper:
      - [Healing Armlet, "+20% Heal Recv"]
      - [Redemption Armlet, "+15% DMG in Pos 1, -3% Virtue"]
      - [Fortunate Armlet, "+8 ACC, +3% CRIT, +10% Stress"]
      - [Immunity Mask, "+40% Stun Res, +30% Blight/Bleed Res, -10% Max HP"]
      - [Berserk Mask, "+8% CRIT, +3 SPD, -10% Virtue, -33% Heal Recv"]
      - [Petrified Amulet, "+10 ACC if Bandage, +15% Max HP, -15% Bleed Res"]
    Man_at_Arms:
      - [Cleansing Eyepatch, "+30% Blight Res, +20% Disease Res, -2 DODGE"]
      - [Sly Eyepatch, "+4 DODGE, -10% Stun/Move Res"]
      - [Longevity Eyepatch, "+15% Max HP, -2 SPD"]
      - [Rampart Shield, "+40% Move Skill, +30% Stun Skill, -15% DMG"]
      - [Guardian's Shield, "If in Pos 4: +10% PROT, +50% Heal Recv, +10 DODGE"]
      - [Mirror Shield, "+10 DODGE, 30% DMG Reflection, +20% Stun Res"]
    Occultist:
      - [Eldritch Killing Incense, "+6% CRIT & +15% DMG vs Eldritch"]
      - [Evasion Incense, "+8 DODGE, -1 SPD"]
      - [Cursed Incense, "+40% Debuff Skill, +20% Move Skill, -10% Max HP"]
      - [Sacrificial Cauldron, "+20% DMG, +10% Stress"]
      - [Demon's Cauldron, "+30% Stun Skill, +40% Debuff Skill, +3% CRIT, +15% Stress"]
      - [Petrified Skull, "+30..40% PROT vs Eldritch/Husk, -20% Heal Recv, +15% Max HP"]
    Plague_Doctor:
      - [Diseased Herb, "+40% Disease Res"]
      - [Rotgut Censer, "+8 ACC, -5% Max HP"]
      - [Witch's Vial, "+15% Stun Skill"]
      - [Poisoned Herb, "+40% Blight Skill, -15% Max HP"]
      - [Bloody Herb, "+10 Melee ACC, +30% Bleed Skill, +20% Melee DMG"]
      - [Blasphemous Vial, "+10 Ranged ACC, +20% Stun Skill, +20% Blight Skill, +25% Stress"]
      - [Ashen Distillation, "+20 DODGE, +25% Blight Skill, +20% Heal Recv if Herbs"]
    Shieldbreaker:
      - [Venomous Vial, "+30% Blight Skill, -10% Blight Res"]
      - [Shimmering Scale, "+10% PROT, +5% Stress"]
      - [Dancer's Footwraps, "+40% Move Res, +2 SPD"]
      - [Fanged Spear Tip, "+35% DMG vs Marked, -10% DMG"]
      - [Cuirboilli, "+33% Max HP, -2 SPD"]
      - [Spectral Speartip, "+15% DMG, +20% Blight Skill, +15% Max HP, +5% Random Target"]
      - [Obsidian Dagger, "+40% Debuff Skill, +40% Blight Skill"]
      - [Severed Hand, "+50% Blight Res, -10% Stress"]
    Vestal:
      - [Virtuous Chalice, "+10% Virtue, -5% Max HP"]
      - [Haste Chalice, "+8 SPD R1, +2 SPD after R1, -25% Stun Skill"]
      - [Youth Chalice, "+20% Max HP, -10% DMG"]
      - [Profane Scroll, "+15% DMG, +15% Stress; If Pos 2: +10% PROT, +33% Heal Skills"]
      - [Tome of Holy Healing, "+25% Heal Skills, -15% Max HP"]
      - [Sacred Scroll, "-10% Stress, +33% Heal Skills, -10% Stun Skill, -33% DMG"]
      - [Heretical Passage, "+20% Heal Skills if Holy Water, +25% DMG vs Husk/Eldritch, +10% Stress"]

  dlc_and_unique:
    - [Lens of the Comet, "Ignores Stealth, -20% Virtue, +5% CRIT if Shard Dust"]
    - [Crystal Pendant, "+15% Shards Given, +15% Stress"]
    - [Cluster Pendant, "+25% Shards Given, +15% Stress"]
    - [Coat Of Many Colors, "On Kill: -2% Stress & +2 ACC (2 Battles)"]
    - [Miller's Pipe, "On Kill: Stress -2, All Monsters: Blight 2/3rd"]
    - [Mildred's Locket, "Miller: The Reaping -100% DMG Taken, +40% Blight Res, +3 SPD, +40% DMG vs Miller"]
    - [Thing's Mesmerizing Eye, "+4% CRIT if HP >41%, +8% CRIT if HP <40%"]
    - [Crystalline Fang, "+10% Stun Skill if HP >40%, +40% Stun Skill if HP <41%"]
    - [Phase Shifting Hide, "-15% Stress if HP >41%, -50% Stress if HP <40%"]
    - [Prismatic Heart Crystal, "+35% Blight/Bleed Skill vs Thing, +12% CRIT vs Thing"]
    - [Ancestor's Vintage, "Delayed Curse craving duration"]
    - [Coven Signet, "-25% Stress if has Crimson Curse"]
    - [Dazzling Mirror, "+4 SPD vs Bloodsuckers, +20% Stun Skill vs Bloodsuckers"]
    - [Mantra of Fasting, "+40% Max HP & +7 SPD if Wasting"]
    - [Mercurial Salve, "+25% DMG vs Bloodsuckers"]
    - [Pagan Talisman, "+25% DMG vs Fanatic, -10% Stress"]
    - [Rat Carcass, "Immune to death by Crimson Curse"]
    - [Sanguine Snuff, "+8% CRIT & +15 DODGE if Bloodlust"]
    - [Sculptor's Tools, "+40% DMG vs Stonework"]

  crimson_court_sets:
    Abomination: ["Shameful Shroud (-15% Stress, +10 DODGE)", "Osmond Chain (+20% Ranged DMG, +8% Ranged CRIT)", "Set: +20% DMG in Pos 1"]
    Antiquarian: ["The Master's Essence (+50% Heal Skills, +35% Blight/Debuff Skill)", "Two of Three (+50% DMG vs Blighted, +8% CRIT vs Blighted)", "Set: +4 SPD, +10 DODGE"]
    Arbalest: ["Childhood Treasure (+30% Heal Skills, +20% Camp Heal Skills, -15% Stress)", "Bedtime Story (+15 ACC vs Marked, +8% CRIT vs Marked, +35% Debuff/Move Skill)", "Set: +25% PROT"]
    Bounty_Hunter: ["Crime Lords' Molars (+20% DMG vs Marked/Stunned/Bleeding, -10 DODGE)", "Vengeful Kill List (+50% Move Skill, +35% Bleed Skill, +15 Ranged ACC)", "Set: +5% CRIT vs Marked/Stunned/Bleeding"]
    Crusader: ["Glittering Spaulders (+15% PROT, +35% Move Res, -15% Stress, -2 SPD)", "Signed Conscription (+20% Heal Skills, +20% Stress Skills)", "Set: +20% Max HP"]
    Flagellant: ["Chipped Tooth (+20% Max HP, +35% Move Res)", "Shard of Glass (+35% Bleed Skill, -20% Bleed Res)", "Set: +10% Deathblow Res"]
    Grave_Robber: ["Absinthe (+35% Disease/Blight Res, +35% Blight Skill, -10% Max HP)", "Sharpened Letter Opener (+25% Melee DMG, +10 Melee ACC, +5 DODGE)", "Set: +5% CRIT"]
    Hellion: ["Lioness Warpaint (+20% DMG per HP loss, +10% Stress)", "Mark of the Outcast (+2 SPD, +35% Bleed Skill, +15% Deathblow Res, -15% Heal Recv)", "Set: +7 ACC, +7 DODGE"]
    Highwayman: ["Bloodied Neckerchief (+2 SPD, +10 DODGE)", "Shameful Locket (+10 ACC, +5% CRIT, +15% Stress)", "Set: +45% Virtue"]
    Houndmaster: ["Evidence of Corruption (+25% Scouting, -15% Surprise, +10% Stress)", "Battered Lawman's Badge (+15 Ranged ACC, +50% Camp Stress, +25% Heal Skills, -20% Stun/Debuff Res)", "Set: +25% DMG vs Bleeding, +5% CRIT vs Bleeding"]
    Jester: ["Tyrant's Tasting Cup (+33% Stress Skills, +25% Stress)", "Tyrant's Fingerbone (+3 SPD in Pos 1, +20 DODGE in Pos 1)", "Set: +33% Camp Stress Skills"]
    Leper: ["Last Will and Testament (+15% PROT, +15% Max HP, -10% Deathblow Res)", "Tin Flute (-20% Stress, +33% Camp Stress Skills)", "Set: +15 ACC if HP >60%"]
    Man_at_Arms: ["Old Unit Standard (+15% Stun Skill, +20% Debuff Skill, +15% Deathblow Res, +10% Stress)", "Toy Soldier (+10% PROT, +5% CRIT)", "Set: Riposte +25% DMG & +10 ACC"]
    Musketeer: ["Second Place Trophy (+30% Heal Skills, +20% Camp Heal Skills, -15% Stress)", "Silver Musket Ball (+15 ACC vs Marked, +8% CRIT vs Marked, +35% Debuff/Move Skill)", "Set: +25% PROT"]
    Occultist: ["Blood Pact (+4 SPD & +25% DMG if Torch <60, -25% Bleed Skill, -10% Max HP)", "Vial of Sand (+20% Debuff/Stun/Move Skill, +20% Stun Res)", "Set: +15 DODGE"]
    Plague_Doctor: ["Subject #40 Notes (+25% Max HP, +35% Disease Res)", "Dissection Kit (+35% Bleed Skill, +25% DMG)", "Set: +15% Blight/Stun Skill"]
    Shieldbreaker: ["Obsidian Dagger (+40% Debuff/Blight Skill)", "Severed Hand (+50% Blight Res, -10% Stress)", "Set: +15% Max HP, +10% PROT, Can't be Guarded"]
    Vestal: ["Atonement Beads (+15% Melee DMG, +8% Melee CRIT, -15% Virtue)", "Salacious Diary (+33% Camp Stress Skills, +25% Heal Skills)", "Set: +35% Debuff/Stun Skill"]


```

---

### EVALUATION OUTPUT FORMAT

You MUST output strictly valid JSON matching the following schema:

```json
{
  "positional_legality": {
    "pos_4_eval": {
      "hero": "<string>",
      "starting_pos": 4,
      "skills_verification": {
        "<skill_name_1>": {"launch_ranks": [<int>], "is_usable": <bool>},
        "<skill_name_2>": {"launch_ranks": [<int>], "is_usable": <bool>},
        "<skill_name_3>": {"launch_ranks": [<int>], "is_usable": <bool>},
        "<skill_name_4>": {"launch_ranks": [<int>], "is_usable": <bool>}
      },
      "all_skills_usable": <bool>,
      "hero_positional_score": <float 0.0 or 0.75>
    },
    "pos_3_eval": {
      "hero": "<string>",
      "starting_pos": 3,
      "skills_verification": {
        "<skill_name_1>": {"launch_ranks": [<int>], "is_usable": <bool>},
        "<skill_name_2>": {"launch_ranks": [<int>], "is_usable": <bool>},
        "<skill_name_3>": {"launch_ranks": [<int>], "is_usable": <bool>},
        "<skill_name_4>": {"launch_ranks": [<int>], "is_usable": <bool>}
      },
      "all_skills_usable": <bool>,
      "hero_positional_score": <float 0.0 or 0.75>
    },
    "pos_2_eval": {
      "hero": "<string>",
      "starting_pos": 2,
      "skills_verification": {
        "<skill_name_1>": {"launch_ranks": [<int>], "is_usable": <bool>},
        "<skill_name_2>": {"launch_ranks": [<int>], "is_usable": <bool>},
        "<skill_name_3>": {"launch_ranks": [<int>], "is_usable": <bool>},
        "<skill_name_4>": {"launch_ranks": [<int>], "is_usable": <bool>}
      },
      "all_skills_usable": <bool>,
      "hero_positional_score": <float 0.0 or 0.75>
    },
    "pos_1_eval": {
      "hero": "<string>",
      "starting_pos": 1,
      "skills_verification": {
        "<skill_name_1>": {"launch_ranks": [<int>], "is_usable": <bool>},
        "<skill_name_2>": {"launch_ranks": [<int>], "is_usable": <bool>},
        "<skill_name_3>": {"launch_ranks": [<int>], "is_usable": <bool>},
        "<skill_name_4>": {"launch_ranks": [<int>], "is_usable": <bool>}
      },
      "all_skills_usable": <bool>,
      "hero_positional_score": <float 0.0 or 0.75>
    },
    "subscore": <float 0.0-3.0>
  },
  "tactical_synergy": {
    "backline_reach": {
      "skills_targeting_r3_r4": ["<skill_name>"],
      "assessment": "<string>",
      "score": <float 0.0, 0.5, or 1.0>
    },
    "crowd_control": {
      "active_stuns": ["<skill_name>"],
      "assessment": "<string>",
      "score": <float 0.0, 0.5, or 1.0>
    },
    "repositioning_and_combos": {
      "moves_pulls_pushes": ["<skill_name>"],
      "speed_tiers": "<string>",
      "damage_combos": "<string>",
      "score": <float 0.0, 0.5, or 1.0>
    },
    "subscore": <float 0.0-3.0>
  },
  "trinket_compatibility": {
    "pos_4_trinkets": {"trinkets": ["<t1>", "<t2>"], "dead_passives_found": <bool>, "penalties_or_conflicts": "<string>", "hero_trinket_score": <float 0.0 or 0.5>},
    "pos_3_trinkets": {"trinkets": ["<t1>", "<t2>"], "dead_passives_found": <bool>, "penalties_or_conflicts": "<string>", "hero_trinket_score": <float 0.0 or 0.5>},
    "pos_2_trinkets": {"trinkets": ["<t1>", "<t2>"], "dead_passives_found": <bool>, "penalties_or_conflicts": "<string>", "hero_trinket_score": <float 0.0 or 0.5>},
    "pos_1_trinkets": {"trinkets": ["<t1>", "<t2>"], "dead_passives_found": <bool>, "penalties_or_conflicts": "<string>", "hero_trinket_score": <float 0.0 or 0.5>},
    "subscore": <float 0.0-2.0>
  },
  "sustain_and_recovery": {
    "hp_sustain": "<string>",
    "hp_sustain_score": <float 0.0, 0.5, or 1.0>,
    "stress_sustain": "<string>",
    "stress_sustain_score": <float 0.0, 0.5, or 1.0>,
    "subscore": <float 0.0-2.0>
  },
  "final_score": <float 0.0-10.0>
}

```

```