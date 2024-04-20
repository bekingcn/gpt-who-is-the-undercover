import time, random
from langchain.adapters.openai import convert_openai_messages
from langchain_openai import ChatOpenAI
model_name = "gpt-3.5-turbo"

from langchain_core.pydantic_v1 import BaseModel
from typing import Annotated, Sequence, Dict
import operator

"""
In the "Who is the undercover" game, 
a group of n (where n is greater than or equal to 3) players are divided into "innocent" players and "undercover" players. 
The "innocent" players receive the same word, while the "undercover" players receive a similar but different word. 
Each player can only make one statement per round to describe their word without directly revealing it, 
providing hints to their allies without giving away their identity to the undercover players. 
After each round of statements, players vote to eliminate who they suspect is the undercover player. 
The player with the most votes is eliminated, with ties leading to the next round. 
If only three players remain (including the undercover player), the undercover player wins; 
otherwise, the innocents win.
"""
from .gameconfig import GLOBAL_GAME_CONFIG
from .gameconfig import REORDER_METHOD_SHIFT, REORDER_METHOD_SHUFFLE
from .gameconfig import REORDER_PLAYERS_NOTHING, REORDER_PLAYERS_EVERY_ROUND, REORDER_PLAYERS_EVERY_TASK

TASK_NAME_KICKOFF = "kickoff"
TASK_NAME_STATEMENT = "statement"
TASK_NAME_VOTE = "vote"
TASK_NAME_END = "end"
TASK_NAME_NEW = "new"

ROUTER_EVENT_NAME_KICKOFF = "kickoff"
ROUTER_EVENT_NAME_GAME_END = "game over"
ROUTER_EVENT_NAME_ROUND_END = "round over"
ROUTER_EVENT_NAME_STATEMENT_END = "statemente over"
ROUTER_EVENT_NAME_VOTE_END = "vote over"
ROUTER_EVENT_NAME_ROUND_START = "round start"
ROUTER_EVENT_NAME_TASK_START = "task start"

FINAL_RESULT_INNOCENT_WIN = "innocents winned"
FINAL_RESULT_UNDERCOVER_WIN = "undercover winned"
FINAL_RESULT_QUIT_WRONG_VOTE = "quit with wrong vote"

PLAYER_INDEX_KICKOFF = -1
PLAYER_INDEX_ROUTER = -2

class PlayerData(BaseModel):
    index: int
    name: str
    is_human: bool
    statement_order: int
    vote_order: int
    discussion_order: int

"""
The `GameState` class represents the state of a game of Undercover. It holds the following attributes:
- `players_num`: The number of players in the game.
- `current_turn`: The index of the player whose turn it is.
- `innocent_word`: The word given to the innocent players.
- `undercover_word`: The word given to the undercover player.
- `alive_players`: A list of indices representing the players who are still alive.
- `players_order`: A randomly generated order of the players.
- `alive_status`: A list of booleans representing the status of each player (alive or not).
- `players_words`: A list of strings representing the word each player has.
- `statements`: A list of strings representing the statements each player has made.
- `votes`: A list of integers representing the vote each player has made.
- `history`: A list of dictionaries representing the history of turns.
"""
class GameState(BaseModel):
    # user input
    players_num: int
    # initialize with the number of players
    players: Sequence[PlayerData]
    # kickoff's output
    innocent_word: str
    undercover_word: str
    players_words: Sequence[str]


    # judge and fills by router output
    # reorder players every round or every task due to config
    players_order: Sequence[int]
    alive_status: Sequence[bool]
    turn: int = 0
    current_task: str = TASK_NAME_NEW
    final_result: str
    
    # fill by player index
    statements: Sequence[str]
    votes: Sequence[int]

    # append by router in the end of round
    history: Annotated[Sequence[dict], operator.add]
    
    # fill by player router
    # next player index with current task, or -1 if there is no next player
    next_player_index: int
    
    @classmethod
    def init_state(cls, players_num: int):        
        order = list(range(players_num))
        statement_order = cls._create_order(order, type="shuffle")
        vote_order = statement_order
        discussion_order = statement_order
        human_players = random.sample(range(players_num), 1)
        return {
            "players_num": players_num,
            "players": [
                PlayerData(
                    index=i, 
                    name=f"Human-{i}" if i in human_players else f"AI-{i}", 
                    is_human= (i in human_players),
                    statement_order=statement_order.index(i), 
                    vote_order=vote_order.index(i), 
                    discussion_order=discussion_order.index(i), 
                ) for i in range(players_num)],
            "innocent_word": "",
            "undercover_word": "",
            "players_words": [],
            "players_order": statement_order,
            "alive_status": [True] * players_num,   # must write here, not working if with a variable, why?
            "turn": 0,
            "current_task": "",
            "statements": [""] * players_num,
            "votes": [-1] * players_num,
            "history": [],
            "final_result": "",
            # here -1 means no next player
            "next_player_index": -1,
        }
    
    def is_alive(self, player_index):
        return self.alive_status[player_index]
    
    # @property
    def statements_order(self):
        self._order_players_by("statement")

    @property
    def alive_players(self):
        return [p for p, a in zip(self.players, self.alive_status) if a == True]
        
    def _order_players_by(self, order_type="statement", new_alive_status=None):
        # here new_alive_status to get next round's order
        alive_status = new_alive_status or self.alive_status
        # re-order players' index with player's statement order
        if order_type == "statement":
            ord1 = [(p.statement_order, p.index) for p, a in zip(self.players, alive_status) if a == True]
        elif order_type == "vote":
            ord1 = [(p.vote_order, p.index) for p, a in zip(self.players, alive_status) if a == True]
        elif order_type == "discussion":
            ord1 = [(p.discussion_order, p.index) for p, a in zip(self.players, alive_status) if a == True]
        sorted_ord1 = sorted(ord1, key=lambda x: x[0])
        return [i[1] for i in sorted_ord1]

    @classmethod
    def _create_order(cls, order: list[int], type=None) -> list[int]:
        # shuffle or shift
        type = type or GLOBAL_GAME_CONFIG.order_players_by
        if type == "shuffle":
            new_order = order.copy()
            random.shuffle(new_order)
            return new_order
        elif type == REORDER_METHOD_SHIFT:
            starter = random.randint(0, len(order)-1)
            new_order = order[starter:]
            new_order.extend(order[:starter])
            return new_order
        raise NotImplementedError("Invalid order type")

class BasePlayerAgent:
    def __init__(self, player: PlayerData, callback=None, rounds_history=False):
        self.callback = callback or self._callback
        self.player = player
        self.player_index = player.index
        self.rounds_history = rounds_history

    def _callback(self, player_index, task, task_output, state=None):
        if task == TASK_NAME_STATEMENT:
            print(f"Player {self.player_index}: {task_output}")
        elif task == TASK_NAME_VOTE:
            print(f"Player {self.player_index}: Vote {task_output}")
    
    def run(self, state: GameState):
        current_task = state.current_task
        # if not alive, return None
        if state.alive_status[self.player_index] == False:
            print(f"Player {self.player_index} is not alive")
            return None
        
        word = state.players_words[self.player_index]
        if current_task == "statement":
            statement = self._run_statement(state)
            self.callback(self.player_index, current_task, {"statement": statement}, state)
            return {
                "statements": [statement if i == self.player_index else s for i, s in enumerate(state.statements)]
            }
        elif current_task == "vote":
            vote, response = self._run_vote(state)
            self.callback(self.player_index, current_task, response, state)
            return {
                "votes": [vote if i == self.player_index else v for i, v in enumerate(state.votes)]
            }
        raise Exception("Invalid current task")
        
    def _run_statement(self, state: GameState):
        raise NotImplementedError("Must implement _run_statement")

    def _run_vote(self, state: GameState):
        raise NotImplementedError("Must implement _run_vote")
    
    def _all_history(self, state: GameState, with_votes=True, with_history_in_rounds=True):
        # TODO: combine with rounds' history
        if self.rounds_history:
            result = self._history_in_rounds_list(state, with_votes)
            result.append((f"Round {state.turn}", self._history_list(state, with_votes)))
            return result
        return self._history_list(state, with_votes)
    
    # TODO: move these into GameState
    def _history(self, order, statements, votes=None): 
        for p in order:
            # filter out empty statements
            if statements[p]:
                # filter out negative votes, which means that the player didn't vote
                if votes is not None and votes[p] >= 0:
                    yield {"player": p, "statement": statements[p], "voted-to-player": votes[p]}
                else:
                    yield {"player": p, "statement": statements[p]}
    
    def _history_list(self, state: GameState, with_votes=True):
        return list(self._history(state.players_order, state.statements, state.votes if with_votes else None))
    
    def _history_in_rounds(self, state: GameState, with_votes=True):
        order = state.players_order
        for r in state.history:
            data = []
            statements = r.get("statements")
            if with_votes:
                votes = r.get("votes")
                for p in order:
                    data.append({"player": p, "statement": statements[p], "voted-to-player": votes[p]})
            else:
                for p in order:
                    data.append({"player": p, "statement": statements[p]})
            yield f"Round {r.get('turn')}", data
    
    def _history_in_rounds_list(self, state: GameState, with_votes=True):
        return list(self._history_in_rounds(state, with_votes=with_votes))
    

# ==== TESTS =====

def test_orders():
    data = GameState.init_state(5)
    state = GameState.parse_obj(data)
    orig_order = data["players_order"]
    new_order = state.get_players_order()
    print("orig order", orig_order)
    print("new order", new_order)
    assert orig_order == new_order
    
    state.alive_status[3] = False
    new_order = state.get_players_order()
    print("new order", new_order)
    assert 3 not in new_order

if __name__ == "__main__":
    test_orders()

