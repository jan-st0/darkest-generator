from game_data_manager import GameDataManager


if __name__ == "__main__":
    man = GameDataManager()
    types = {
        skill.target_type
        for skill in man.all_combat_skills()
    }
    print(types)