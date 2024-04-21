import streamlit as st
import sys
import threading
import time
from langchain_core.runnables import RunnableConfig
import queue
from langgraph.graph.graph import CompiledGraph

from agents.base import TASK_NAME_KICKOFF, TASK_NAME_STATEMENT, TASK_NAME_VOTE, GameState
from agents.base import ROUTER_EVENT_NAME_GAME_END, ROUTER_EVENT_NAME_ROUND_END, \
    ROUTER_EVENT_NAME_KICKOFF, ROUTER_EVENT_NAME_STATEMENT_END, ROUTER_EVENT_NAME_VOTE_END, \
    ROUTER_EVENT_NAME_ROUND_START, ROUTER_EVENT_NAME_TASK_START, \
    PLAYER_INDEX_ROUTER, PLAYER_INDEX_KICKOFF

from agents.gameconfig import GLOBAL_GAME_CONFIG as game_config
from config import config as os_config, DEBUG, logger
from utils import MyQueue, Empty

# indicate if we should render it in the UI
PLAYER_INDEX_UI_ERROR = -100
PLAYER_INDEX_UI_NOT_RENDER = -99
PLAYER_INDEX_UI_RENDER = -98
GAMES_PATH = "games"
GITHUB_URL = "https://github.com/bekingcn/gpt-who-is-the-undercover"

def st_callback(st_q):
    def _callback_wrapper(player_index, task, task_output, state):
        st_q.put({"player_index": player_index, "task": task, "task_output": task_output, "state": state})
    return _callback_wrapper

def st_user_callback(st_q, st_input_q):
    # put a new message into the message queue
    def _callback_wrapper(player_index, state, **kwargs):
        logger.debug(f"CALLBACK: {player_index}, {state.current_task}")
        st_q.put({"player_index": player_index, "task": f"user-{state.current_task}", "task_output": kwargs, "state": state})
        return st_input_q
    return _callback_wrapper


def format_players_order(players, order=None):
    if order is None:
        order = list(range(len(players)))
    text = ""
    for i in order:
        p = players[i]
        if p.is_human:            
            text = text + f"\n- **{p.name:<15} (id: {i:<3}, YOU)**"
        else:
            text = text + f"\n- {p.name:<15} (id: {i:<3}, AI)"
    return text

# is it a debug msg?
def render_message(msg, json_obj=None, debug_mode=False, expanded=False):
    if msg:
        st.markdown(msg)
    if json_obj and debug_mode:
        st.json(json_obj, expanded=expanded)


def format_message(player_index, task, task_output, state, debug_mode):
    """Format the message to display for a given player and task."""
    logger.debug(f"MSG_RENDER: {player_index}, {task}, {task_output}")

    if player_index == PLAYER_INDEX_UI_NOT_RENDER:
        return None, None

    if player_index == PLAYER_INDEX_UI_RENDER:
        if task == "END":
            text, json_obj = _format_end_task(state)
        else:
            text, json_obj = None, None
        return text, json_obj

    if player_index >= 0:
        text, json_obj = _format_agent_task(player_index, task, task_output, state)
        return text, json_obj

    if player_index == PLAYER_INDEX_KICKOFF:
        text, json_obj = _format_kickoff_task(task, task_output, state)
        return text, json_obj

    if player_index == PLAYER_INDEX_ROUTER:
        text, json_obj = _format_router_task(task, task_output, state)
        return text, json_obj

    logger.debug(state.json())
    logger.debug(f"MSG_RENDER: {player_index}, {task}, {task_output}")
    raise Exception("Invalid player index or task")


def _format_end_task(state):
    # render the result: final result, leftover players, words for each player, etc
    names = [player.name for player in state.players]
    zipped = list(zip(names, state.alive_status, state.players_words))
    zipped.sort(key=lambda x: x[1])
    text_players = "\n  - ".join([f"{name:<15} ({"alive" if alive else "out of game"}, word: {word})" for name, alive, word in zipped])
    text = f"""
#### Game is Over
- Result: {state.final_result}
- Leftover Players: 
  - {text_players}
"""
    json_obj = state.dict()
    return text, json_obj


def _format_agent_task(player_index, task, task_output, state):
    player_name = state.players[player_index].name
    player_desc = f"{player_name} (id: {player_index})"

    if task == TASK_NAME_STATEMENT:
        text = _format_statement_task(player_desc, task_output)
    elif task == TASK_NAME_VOTE:
        text = _format_vote_task(player_desc, task_output)
    else:
        text = None

    return text, None


def _format_statement_task(player_desc, task_output):
    statement = task_output.get('statement')
    return f"""\
#### Player {player_desc} Statement
{statement}"""


def _format_vote_task(player_desc, task_output):
    vote = task_output.get('vote')
    reason = task_output.get('reason')
    return f"""\
#### Player {player_desc} Vote
- Vote to: {vote}
- Reason: {reason}"""


def _format_kickoff_task(task, task_output, state):
    if task == TASK_NAME_KICKOFF:
        players_with_order = format_players_order(state.players, order=task_output.get('order'))
        text = f"""\
#### Kickoff Game with {len(state.players)} Players
**The order of players:**
{players_with_order}

"""
    return text, task_output

def _format_router_task(task, task_output, state):
    event = task_output.get("event")

    if event == ROUTER_EVENT_NAME_KICKOFF:
        text = None
    elif event == ROUTER_EVENT_NAME_STATEMENT_END:
        text = None
    elif event == ROUTER_EVENT_NAME_VOTE_END:
        text = _format_vote_end_task(task_output, state)
    elif event == ROUTER_EVENT_NAME_GAME_END:
        text = None
    elif event == ROUTER_EVENT_NAME_ROUND_END:
        text = "---"
    elif event == ROUTER_EVENT_NAME_ROUND_START:
        text = _format_round_start_task(task_output, state)
    elif event == ROUTER_EVENT_NAME_TASK_START:
        text = _format_task_start_task(task_output, state)
    else:
        text = None

    return text, task_output


def _format_vote_end_task(task_output, state):
    player_index = task_output.get('player_out_of_game')
    player_name = state.players[player_index].name
    is_human = state.players[player_index].is_human
    return f"""\
#### Vote Result:
- Out of game: {player_name} (id: {player_index})
- Role: {"**YOU**" if is_human else "AI"}"""


def _format_round_start_task(task_output, state):
    players_with_order = format_players_order(state.players, order=task_output.get("players_order", None))
    return f"""\
#### Round {state.turn} - Start by order:
{players_with_order}"""


def _format_task_start_task(task_output, state):
    players_with_order = format_players_order(state.players, order=task_output.get("players_order", None))
    return f"""\
#### Round {state.turn} - Stage: {state.current_task} - Start by order:
{players_with_order}"""

# handle user input
def on_human_input():
    app_state: AppState = st.session_state["app_state"]
    if "statement_input" in st.session_state  and st.session_state["statement_input"]:
        # clear the key
        value = st.session_state.pop("statement_input")
        # TODO: to align the output from user call, like:
        # st.session_state["input_queue"].put({"statement": value})
        app_state.input_queue.put(value)
        return
    if "vote_input" in st.session_state and st.session_state["vote_input"]:
        # clear the key
        value = st.session_state.pop("vote_input")
        value = value.index # int(value)
        # should be a tuple :<
        app_state.input_queue.put(tuple([value, {"vote": value}]))
        return
    raise NotImplementedError("Invalid input")

# render user input
def render_human_input(player_index, state: GameState, **kwargs):
    word = state.players_words[player_index]
    player_name = state.players[player_index].name
    # add a container to make the input box in the flow, instead of the bottom
    with st.container():
        if state.current_task == "statement":
            st.chat_input(
                f"You are {player_name} (id: {player_index}, word: {word}), please input your statement: ",
                key=f"statement_input",
                on_submit=on_human_input)
            return
        if state.current_task == "vote":
            players = state.alive_players
            st.selectbox("Who do you want to vote?", 
                         players, 
                         key=f"vote_input",
                         index=None,
                         on_change=on_human_input,
                         label_visibility="hidden",
                         placeholder="Who do you want to vote?",
                         format_func=lambda x: f"{x.name} (id: {x.index}) - YOU" if x.index == player_index else f"{x.name} (id: {x.index})")
            return
        raise NotImplementedError("Invalid input task")

def select_players_num():
    """
    Function to handle players number selection in Streamlit app.
    If players number is selected, it initializes the game and starts running the graph.
    """
    global debug_mode
    # Get the selected players number from the session state
    players_num = st.session_state.players_num
    with_human_player = st.session_state.with_human_player
    with_rounds_history = st.session_state.with_rounds_history
    order_players_by = st.session_state.order_players_by
    reorder_players_every = st.session_state.reorder_players_every
    player_agents_connect_with = st.session_state.player_agents_connect_with
    timeout_for_human = st.session_state.timeout_for_human
    debug_mode = st.session_state.debug_mode
    
    # use user's openai api key and base url
    openai_api_key = st.session_state.openai_api_key
    openai_base_url = st.session_state.openai_base_url
    logger.info("User's OpenAI API key: %s", bool(openai_api_key is not None))
    os_config(openai_api_key=openai_api_key, openai_base_url=openai_base_url)
    
    # TODO: reset, to clear the selection
    # st.session_state.pop("players_num")
    
    from graph import graph
    
    if players_num:                    
        # Initialize the game graph
        config = RunnableConfig(recursion_limit=120, max_concurrency=1)
        init_data = GameState.init_state(players_num)
        
        # change settings
        global game_config
        game_config.with_humans = 1 if with_human_player else 0
        game_config.round_history = with_rounds_history
        game_config.order_players_by = order_players_by
        game_config.reorder_palyers = reorder_players_every
        game_config.player_agents_connect_with = player_agents_connect_with
        game_config.human_input_timeout = timeout_for_human
        # TODO: remove it
        history_words = [
            ["Piano", "Accordion"],
            ["Butterfly", "Moth"],
            ["Books", "Magazines"],
            ["Beach", "Desert"],
            ["Ice Cream", "Sorbet"],
            ["The Eiffel Tower", "The Great Wall of China"],
        ] + st.session_state["history_words"]
        game_config.word_pair_examples = history_words
        
        app_state: AppState = st.session_state["app_state"]
        # NOTE: have to restart it, we support a new app_id for each run
        # so we can serialize the app_state to disk and load it later
        app_state.restart()
        st_q = app_state.message_queue
        st_input_q = app_state.input_queue
        # clear all messages
        st_q.clear()
        g = graph(
            init_data, 
            callback=st_callback(st_q=st_q),
            user_callback=st_user_callback(st_q=st_q, st_input_q=st_input_q),
            with_human=with_human_player, 
            rounds_history=with_rounds_history
        )
        # run as a thread
        def _thread_func():
            try:
                result = g.invoke(init_data, config)
                state = GameState.parse_obj(result)
            except Exception as e:
                # notify the UI to show the error from the queue
                logger.exception(e)
                state =  GameState.parse_obj(init_data)
                exc_info = sys.exc_info()
                st_q.put({"player_index": PLAYER_INDEX_UI_ERROR, "task": "ERROR", "task_output": {"error": str(e), "exc_info": str(exc_info)}, "state": state})
                # notify the UI to end the game
                st_q.put({"player_index": PLAYER_INDEX_UI_RENDER, "task": "END", "task_output": {}, "state": state})
                return
            st_q.put({"player_index": PLAYER_INDEX_UI_RENDER, "task": "END", "task_output": {}, "state": state})
            # Notify the UI to save the game?
            st_q.put({"player_index": PLAYER_INDEX_UI_NOT_RENDER, "task": "END_SAVE", "task_output": {}, "state": state})

        # TODO: how to end the thread gracefully?
        thread = threading.Thread(target=_thread_func, daemon=True)    # daemon=True ?
        thread.start()
        app_state.set_graph(g, thread)
        
    else:
        st.warning("Please select players number first")


def select_history_game():
    if "history_game" in st.session_state and st.session_state["history_game"]:
        app_id = st.session_state["history_game"]["app_id"]
        # st.session_state.pop("history_game")
        messages = load_game(app_id)
        history_game = AppState.from_history_game(app_id, messages)
        st.session_state["app_state"] = history_game

def redo_message(m):
    """
    A function that takes in a dictionary `m` and returns a modified dictionary `nm`.
    
    Parameters:
        m (dict): A dictionary containing key-value pairs.
        
    Returns:
        dict: A modified dictionary `nm`
        where the value for the key "state" is converted to a dictionary if it is not None. 
        Otherwise, the value remains unchanged.
    """
    import json
    nm = {k: v if k != "state" or v is None else v.dict() for k, v in m.items()}
    return nm
    
def save_game(app_id, q,):
    """
    Save the game with the given app ID and message queue.
    
    Args:
        app_id (str): The ID of the app.
        q (Queue): The message queue containing the game history.
        
    Returns:
        None
        
    This function saves the game history to a JSON file and appends the game information to the "games.json" file.
    It removes unnecessary messages from the queue and saves them in the JSON file.
    The last state from the END task is retrieved and used to create the game information.
    The game information is then inserted at the beginning of the "games.json" file.
    """
    import os, json
    path = os.path.join(GAMES_PATH, app_id)
    file_name = f"{app_id}.json"
    file_path = os.path.join(path, file_name)
    if not os.path.exists(path):
        os.makedirs(path)
    # remove unnecessary messages
    messages = [redo_message(m) for m in q.queue if m["player_index"] != PLAYER_INDEX_UI_NOT_RENDER]
    jstr = json.dumps(messages, indent=2)
    with open(file_path, "w+", encoding="utf-8") as f:
        f.write(jstr)
        
    # get the last state from END task if needed
    final_state = messages[-2]["state"]
        
    # append a game
    file_path = os.path.join(GAMES_PATH, "games.json")
    games = load_games()
    name = f"{final_state.get('innocent_word')} - {final_state.get('undercover_word')} ({final_state.get("players_num")} players)"
    games.insert(0, {
        "app_id": app_id, 
        "name": name, 
        "players_num": final_state.get("players_num"), 
        "created_at": time.ctime(time.time()),
        "words": [final_state.get("innocent_word"), final_state.get("undercover_word")]
        })
    with open(file_path, "w+", encoding="utf-8") as f:
        jstr = json.dumps(games, indent=2)
        f.write(jstr)
        
def load_game(app_id):
    import os, json
    path = os.path.join(GAMES_PATH, app_id)
    file_name = f"{app_id}.json"
    file_path = os.path.join(path, file_name)
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        jstr = f.read()
        messages = json.loads(jstr)
        # TODO: any idea to improve this?
        # convert state from dict to GameState
        messages = [{**m, "state": GameState.parse_obj(m["state"]) if m.get("state") else None} for m in messages]
        return messages
    
def load_games():
    """
    Load the list of games from the 'games.json' file.

    If the file does not exist, it returns an empty list. 
    Otherwise, it reads the contents of the file and parses it as JSON. 
    The parsed JSON is then returned as a list of games, with the most recent 20 games selected.

    Returns:
        list: A list of dictionaries representing the loaded games.
    """
    import os, json
    file_path = os.path.join(GAMES_PATH, "games.json")
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        jstr = f.read()
        games = json.loads(jstr)
        # return 20 more recent
        return games[:20]

def load_history_words(games: list[dict]):
    # get the history words and update the 
    word_pairs = []
    for g in games:
        words = g.get("words")
        if words and words not in word_pairs:
            word_pairs.append(words)
        if len(word_pairs) >= 10:
            break
    return word_pairs

# define a class to hold all status and internal states
class AppState:
    def __init__(self):
        # 
        self.restart()

    def restart(self):
        self.app_id = f"app_{time.time_ns()}"
        self.graph = None
        self.graph_thread = None
        self.input_queue = queue.Queue()
        self.message_queue = MyQueue()
        self.end = False
        self.is_history = False

    def reset_loading(self):
        self.message_queue.reset()
        self.end = False

    def set_graph(self, graph, thread):
        self.graph = graph
        self.graph_thread = thread
    
    @property
    def waiting_when_loading(self):
        return self.is_history or self.graph_thread is not None

    # loop this messages to render them
    @property
    def messages(self):
        self.end = not self.waiting_when_loading
        last_time = time.time()
        while not self.end:
            message = self.message_queue.get(timeout=1)
            no_message = message is None
            if not no_message:
                # set by the thread
                if message["task"] == "END":
                    self.end = True
                yield message
            if not self.is_history:
                # double check end status
                if time.time() - last_time > 2:
                    logger.debug(f"thread is alive: {self.graph_thread.is_alive()}")
                    last_time = time.time()
                if not self.graph_thread.is_alive():
                    self.end = no_message
                if no_message:
                    time.sleep(0.2)
    
    @classmethod
    def from_history_game(cls, app_id, messages):
        app_state = cls()
        app_state.app_id = app_id
        app_state.graph = None
        app_state.graph_thread = None
        app_state.input_queue = None
        app_state.message_queue = MyQueue()
        for message in messages:
            app_state.message_queue.put(message)
        app_state.end = False
        app_state.is_history = True
        return app_state    

def render_messages(debug_mode=False):
    """
    Render the messages in the app state.
    
    This function iterates over the messages in the app state and performs the following actions for each message:
    
    1. Check if the message is a human input message. 
        If it is, render the human input using the `render_human_input` function 
        and update the `player_index` field of the message to `PLAYER_INDEX_UI_NOT_RENDER`.
    2. Check if the message is a save message. 
        If it is, save the game using the `save_game` function 
        with the app ID and message queue from the app state. 
        Update the `task` field of the message to "END_SAVED" and 
        reload the games into the session state. Force a rerun of the Streamlit app.
    3. If the message is neither a human input message nor a save message, 
        format the message using the `format_message` function and 
        render it using the `render_message` function.
    
    """
    import time
    # main logic
    app_state: AppState = st.session_state["app_state"]
    app_state.reset_loading()
    if app_state.waiting_when_loading:
        st.info(f"waiting for messages...")
    
    # TODO: any idea to use st.status here?
    for message in app_state.messages:
        # TODO: it's tricky to process human input, and ensure processing it ONLY ONCE
        # any way to improve it?
        player_index = message["player_index"]
        task = message["task"]
        state = message["state"]
        task_output = message["task_output"]
        # check if it's a human input message
        if player_index >= 0 and (task in ["user-statement", "user-vote"]):     # with task == f"user-{state.current_task}"):
            render_human_input(player_index, state=state)
            message["player_index"] = PLAYER_INDEX_UI_NOT_RENDER
            # this delay is to synchronize timeout with human agent
            # and force to rerun st if no user input
            time.sleep(game_config.human_input_timeout + 0.1)
            st.rerun()
            # continue
        # check if it's a save message
        if player_index == PLAYER_INDEX_UI_NOT_RENDER and task == "END_SAVE":
            save_game(app_state.app_id, app_state.message_queue)
            # change it and will be ignored in the next iteration
            message["task"] = "END_SAVED"
            # reload into the session state
            st.session_state["games"] = load_games()
            st.session_state["history_words"] = load_history_words(st.session_state["games"])
            # force rerun
            st.rerun()
        # error from graph
        if player_index == PLAYER_INDEX_UI_ERROR and task == "ERROR":
            st.error(f"Error: {task_output.get('error')}\n\n{task_output.get('exc_info')}")
            st.markdown("**Got an error! Please restart the game.**")
            break
        else:
            text, json_obj = format_message(player_index, task, task_output, state, debug_mode=debug_mode)
            if not text and not json_obj:
                continue
            render_message(text, json_obj, debug_mode=debug_mode)
                
    
def main():
    """
    TODO:
        - foramt the msg only once when it's received
    """
    # init a app state, and use it across the application
    if "app_state" not in st.session_state:
        st.session_state["app_state"] = AppState()
    if "games" not in st.session_state:
        st.session_state["games"] = load_games()
        st.session_state["history_words"] = load_history_words(st.session_state["games"])
    if "debug_mode" not in st.session_state:
        debug_mode = False
    else:
        debug_mode = st.session_state["debug_mode"]
    logger.info("UI debug mode: %s", debug_mode)
        
    with st.sidebar:
        st.title("Settings")
        
        st.text_input(
            "OpenAI API key",
            type="password",
            key="openai_api_key",
            placeholder="Paste your OpenAI API key",
            help="You can get your API key from https://platform.openai.com/account/api-keys"
        )
        
        st.text_input(
            "OpenAI base URL (optional)",
            key="openai_base_url",
            placeholder="Your OpenAI proxy URL if needed",
        )

        st.divider()

        st.checkbox(
            "I want to play as the human player",
            value=False,
            key="with_human_player",
            disabled=False
        )

        st.selectbox(
            "Select the number of players to start the game",
            [4, 5, 6, 7, 8, 9, 10],
            index=None,
            on_change=select_players_num,
            key="players_num",
            placeholder="number of players",
        )

        st.divider()

        with st.expander("Advanced settings", expanded=False):

            st.selectbox(
                "Timeout to answer (seconds)",
                [60, 120, 300, 10, 5, 3, 1] if debug_mode else [60, 120, 300, 1],
                index=0,
                # on_change=select_players_num,
                key="timeout_for_human"
            )

            st.selectbox(
                "How to connect the players",
                ["router", "chain"],
                index=0,
                # on_change=select_players_num,
                key="player_agents_connect_with"
            )

            st.selectbox(
                "Reorder players on every",
                [None, "round", "task"],
                index=0,
                # on_change=select_players_num,
                key="reorder_players_every"
            )

            st.selectbox(
                "Reorder the players with",
                ["shuffle", "shift"],
                index=0,
                # on_change=select_players_num,
                key="order_players_by"
            )

            st.checkbox(
                "Use the history of all rounds",
                value=False,
                key="with_rounds_history"
            )

            st.checkbox(
                "Debug mode",
                value=False,
                key="debug_mode"
            )

        st.selectbox(
            "Game history",
            st.session_state["games"],
            index=None,
            key="history_game",
            placeholder="Select a game",
            on_change=select_history_game,
            format_func=lambda x: x.get("name") or x.get("app_id")
        )
        
        st.divider()
        
        st.markdown(f"Give me a star on [GitHub]({GITHUB_URL})! 🙏")

    st.title("Who is the Undercover?")
    render_messages(debug_mode=debug_mode)

if __name__ == "__main__":
    main()