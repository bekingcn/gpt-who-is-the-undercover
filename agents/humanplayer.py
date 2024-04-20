from .base import BasePlayerAgent
from .base import GameState

from .base import GLOBAL_GAME_CONFIG

class HumanPlayerAgent(BasePlayerAgent):
    def __init__(self, player, callback=None, user_callback=None, rounds_history=False):
        super().__init__(player, callback=callback, rounds_history=rounds_history)
        self.user_callback = user_callback or self._user_callback
        
    def _user_callback(self, player_index, state: GameState, **kwargs):
        history = kwargs.get("history", [])
        word = kwargs.get("word", "")
        print(f"History: {history}")
        if state.current_task == "statement":
            statement = input(f"You are Player {player_index} with word {word}, please input your statement: ")
            return statement
        if state.current_task == "vote":
            # try 3 times if the input is not an integer
            for _ in range(3):
                try:
                    vote = int(input(f"You are Player {player_index} with word {word}, please input your vote (must be an integer): "))
                    return vote, {"vote": vote}
                except ValueError:
                    continue
        raise Exception("Invalid current task")
        
    def _run_vote(self, state: GameState):
        history = self._history_list(state, with_votes=True)
        word = state.players_words[self.player_index]
        # vote and a dict
        ret =  self.user_callback(self.player_index, state, word=word, history=history)
        if isinstance(ret, tuple):
            return ret
        else:
            return self._wait_for_input_from_queue(ret, timeout_default=(-1, {"vote": -1}))
    
    def _run_statement(self, state: GameState):
        history = self._history_list(state, with_votes=False)
        word = state.players_words[self.player_index]
        ret =  self.user_callback(self.player_index, state, word=word, history=history)
        if isinstance(ret, str):
            return ret
        else:
            return self._wait_for_input_from_queue(ret, timeout_default="[no statement]")
    
    def _wait_for_input_from_queue(self, q, timeout_default):
        from queue import Empty, Queue
        assert isinstance(q, Queue)
        try:
            ret = q.get(block=True, timeout=GLOBAL_GAME_CONFIG.human_input_timeout)  # n seconds
            return ret
        except Empty:
            return timeout_default