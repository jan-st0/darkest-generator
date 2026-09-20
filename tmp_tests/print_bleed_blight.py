from game_data_manager import GameDataManager


if __name__ == "__main__":
    man = GameDataManager()

    print("=" * 90)
    print("BLEED SKILLS — structured fields vs effects_raw")
    print("=" * 90)
    bleed_structured = 0
    bleed_raw_only = 0
    for hero in man.heroes:
        for skill in hero.combat_skills:
            pts, dur, chance = skill.bleed_values()
            raw = skill.effects_raw.lower()
            has_raw = 'bleed' in raw and 'bleed_resist' not in raw and 'cure' not in raw
            has_struct = pts > 0

            if has_struct or has_raw:
                status = "OK" if has_struct else "!! MISSING STRUCTURED DATA !!"
                if has_struct:
                    bleed_structured += 1
                else:
                    bleed_raw_only += 1
                print(f"  [{status:^30s}]  {hero.class_name:20s} | {skill.name:25s} "
                      f"| pts={pts}  dur={dur}  chance={chance}")
                print(f"  {'':32s}  effects_raw: {skill.effects_raw}")
                print()

    print(f"  SUMMARY: {bleed_structured} with structured data, "
          f"{bleed_raw_only} with raw text only, "
          f"{bleed_structured + bleed_raw_only} total")

    print()
    print("=" * 90)
    print("BLIGHT SKILLS — structured fields vs effects_raw")
    print("=" * 90)
    blight_structured = 0
    blight_raw_only = 0
    for hero in man.heroes:
        for skill in hero.combat_skills:
            pts, dur, chance = skill.blight_values()
            raw = skill.effects_raw.lower()
            has_raw = 'blight' in raw and 'blight_resist' not in raw and 'cure' not in raw
            has_struct = pts > 0

            if has_struct or has_raw:
                status = "OK" if has_struct else "!! MISSING STRUCTURED DATA !!"
                if has_struct:
                    blight_structured += 1
                else:
                    blight_raw_only += 1
                print(f"  [{status:^30s}]  {hero.class_name:20s} | {skill.name:25s} "
                      f"| pts={pts}  dur={dur}  chance={chance}")
                print(f"  {'':32s}  effects_raw: {skill.effects_raw}")
                print()

    print(f"  SUMMARY: {blight_structured} with structured data, "
          f"{blight_raw_only} with raw text only, "
          f"{blight_structured + blight_raw_only} total")
