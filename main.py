import json
from langchain_core.runnables import RunnableConfig
from graph import graph

from agents.base import TASK_NAME_KICKOFF, TASK_NAME_STATEMENT, TASK_NAME_VOTE, GameState

from config import config as os_config, DEBUG, logger
from agents.gameconfig import GameConfig

game_config = GameConfig()

os_config()

# all the game config can be set before creating the graph
game_config.reorder_palyers = "round"
game_config.with_humans = 1     # for now, we support only one human player

# is it a debug msg?
def show_message(msg, debug=False):
    if not debug or DEBUG == debug:
        print(msg)
        print("---")

def my_user_callback(player_index, state: GameState, **kwargs):
    """
    A callback function that is called by the game when it needs user input.
    
    Args:
        player_index (int): The index of the player who is making the input.
        state (GameState): The current state of the game.
        **kwargs: Additional keyword arguments.
        
    Returns:
        str or tuple: If the current task is "statement", returns the user's statement.
                      If the current task is "vote", returns the user's vote as an integer.
                      Raises an Exception if the current task is invalid.
    """
    history = kwargs.get("history", [])
    word = kwargs.get("word", "")
    player_name = state.players[player_index].name
    for h in history:
        text = f"Player {h["player"]}: {h["statement"]}  -  vote: {h.get('vote', '')}"
        show_message(text)
    if state.current_task == "statement":
        statement = input(f"You are {player_name} (id: {player_index}, word: {word}), please input your statement: ")
        return statement
    if state.current_task == "vote":
        # try 3 times if the input is not an integer
        for _ in range(3):
            try:
                vote = int(input(f"You are {player_name} (id: {player_index}, word: {word}), please input your vote (must be an integer): "))
                return vote, {"vote": vote}
            except ValueError:
                continue
    raise Exception("Invalid current task")

def my_callback(player_index, task, task_output, state=None):
    """
    This function is a callback function that handles the output of different tasks during a game. It takes in four parameters:
    
    - `player_index`: An integer representing the index of the player who is executing the task.
    - `task`: A string representing the name of the task being executed.
    - `task_output`: A dictionary containing the output of the task.
    - `state`: An optional parameter representing the state of the game. Default is None.
    
    """
    # indicating that this is the kickoff output.
    if player_index == -1:
        if task == TASK_NAME_KICKOFF:
            hints = f"""
#### Kickoff Words:
- words: {task_output.get('innocent_word')}, {task_output.get('undercover_word')}
- players words: {task_output.get('players_words')})"""
            logger.debug(hints)
            order = task_output.get('order')
            players_with_order = "\n- ".join([f"{state.players[i].name:<15} (index: {i:<3}, human: {state.players[i].is_human})" for i in order])
            text = f"""
#### Kickoff Players and their order:
- {players_with_order}
"""
            show_message(text)
            return
    # playee's output
    # checks the `task` to determine the type of output
    if player_index >= 0:
        player_name = state.players[player_index].name
        player_desc = f"{player_name} (id: {player_index})"
        if task == TASK_NAME_STATEMENT:
            text = f"""
#### Player {player_desc} Statement
{task_output.get('statement')}
            """
            show_message(text)
            return
        if task == TASK_NAME_VOTE:
            text = f"""
#### Player {player_desc} Vote
Vote: {task_output.get('vote')}
Reason : {task_output.get('reason')}
            """
            show_message(text)
            return
    # router's output, with `event` in `task_output` to indicate the type of output
    if player_index == -2:
        # event:
        event = task_output.get("event")
        if event == "kickoff":
            text = json.dumps(task_output, indent=2)
            show_message(text)
            return
        if event == "statemented":
            text = json.dumps(task_output, indent=2)
            show_message(text)
            return
        if event == "voted":
            text = json.dumps(task_output, indent=2)
            show_message(text)
            return
        if event == "game over":
            text = json.dumps(task_output, indent=2)
            show_message(text)
            return
        if event == "round over":
            text = json.dumps(task_output, indent=2)
            show_message(text)
            return
        # more events ignored
        return
    raise Exception("Invalid player index or task")

def render_final_result(result):
    del result["players"]
    from pydantic.json import pydantic_encoder
    text = json.dumps(result, indent=2, default=pydantic_encoder)
    show_message(text)

players_num = input("Please input the number of players: ")
def main(players_num=None):
    config = RunnableConfig(recursion_limit=120)
    init_data = GameState.init_state(players_num, game_config.order_players_by)
    g = graph(
        init_data, 
        game_config=game_config,
        callback=my_callback, 
        user_callback=my_user_callback
    )
    result = g.invoke(init_data, config=config)
    render_final_result(result)
    
    
if __name__ == "__main__":
    main(int(players_num))


