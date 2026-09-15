from game_data_manager import GameDataManager


if __name__ == "__main__":
    man = GameDataManager()
    print('Debuff order in vector:')
    for debuff_type in man.all_debuff_types:
        print(debuff_type, end=' ')
    print('\n')
    print('Buff order in vector')
    for buff_type in man.all_buff_types:
        print(buff_type, end=' ')
    print('\n')
    for skill, vector in man.skills_buff_values.items():
        print(f'{skill.name=}  {vector}')
    print('\n')

    for skill, vector in man.skills_debuff_values.items():
        print(f'{skill.name=}  {vector}')
    