sample_data_7_palyer = {
    'players_num': 7, 
    'alive_status': [True, True, True, True, True, True, True], 
    'history': [], 
    'players_words': ['elephant', 'elephant', 'elephant', 'elephant', 'giraffe', 'elephant', 'elephant'], 
    'turn': 0, 
    'undercover_word': 'giraffe', 
    'statements': [""] * 7, 
    'votes': [-1] * 7, 
    'innocent_word': 'elephant', 
    'players_order': [6, 0, 1, 2, 3, 4, 5],
    'current_task': 'kickoff',
    'final_result': ''
}

sample_data_3_palyer = {
    'players_num': 3, 
    'alive_status': [True, True, True], 
    'history': [], 
    'players_words': ['giraffe', 'elephant', 'elephant'], 
    'turn': 0, 
    'undercover_word': 'giraffe', 
    'statements': [""] * 3, 
    'votes': [-1] * 3, 
    'innocent_word': 'elephant', 
    'players_order': [2, 0, 1],
    'current_task': 'kickoff',
    'final_result': ''
}

sample_data_3_palyer_for_votes = {
    'players_num': 3, 
    'alive_status': [True, True, True], 
    'history': [], 
    'players_words': ['elephant', 'elephant', 'giraffe'], 
    'turn': 0, 
    'undercover_word': 'giraffe', 
    'statements': ['This animal is known for its large ears and powerful trunk.', 'This animal is often associated with intelligence and memory.', 'This animal has a long neck and distinctive spots.'], 
    'votes': [-1] * 3, 
    'innocent_word': 'elephant', 
    'players_order': [2, 0, 1],
    'current_task': 'vote',
    'final_result': ''
}
