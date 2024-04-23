import time, random, json
from langchain.adapters.openai import convert_openai_messages
from langchain_openai import ChatOpenAI
from .base import BasePlayerAgent
from .base import TASK_NAME_KICKOFF, TASK_NAME_STATEMENT, TASK_NAME_VOTE, TASK_NAME_END, TASK_NAME_NEW, GameState
from .prompts import PROMPT_PLAYER_VOTING, PLAYER_VOTING_JSON_FORMAT, PROMPT_PLAYER_STATEMENT

model_name = "gpt-3.5-turbo"
# TODO: reset statements and votes without appending
class AIPlayerAgent(BasePlayerAgent):
    def __init__(self, player, callback=None, rounds_history=False):
        super().__init__(player, callback=callback, rounds_history=rounds_history)
        
    def _run_vote(self, state):
        generated = self.generate_vote(state)
        try:
            vote = int(generated)
            return vote, {"vote": vote}
        except Exception as e:
            result = json.loads(generated)
            return result.get("vote"), result
        return generated
    
    def generate_vote(self, state: GameState):
        word = state.players_words[self.player_index]
        # history_in_rounds = self._history_in_rounds_list(state, with_votes=True)
        history = self._all_history(state, with_votes=True)
        prompt = PROMPT_PLAYER_VOTING
        user_prompt = f"""
This is Round {state.turn}
Here are the statements before your turn in the current round:

{history}

Your word is {word}.
Your index is {self.player_index}.
Make your vote to identify the undercover player's index.

Here is the format of your return:
{PLAYER_VOTING_JSON_FORMAT}
Please return nothing but the JSON.
"""
        prompt[1]["content"] = user_prompt

        lc_messages = convert_openai_messages(prompt)
        response = ChatOpenAI(model=model_name, max_retries=1).invoke(lc_messages).content
        return response
    
    def _run_statement(self, state):
        generated = self.generate_statement(state)
        return generated
    
    def generate_statement(self, state: GameState):
        word = state.players_words[self.player_index]
        # history_in_rounds = self._history_in_rounds_list(state, with_votes=False)
        history = self._all_history(state, with_votes=False)
        prompt = PROMPT_PLAYER_STATEMENT
        user_prompt = f"""
This is Round {state.turn}
Here are the statements before your turn in the current round:

{history}

Your word is {word}.
Your player index is {self.player_index}.
Make your one sentence statement and do not repeat any of the previous statements.
"""
        prompt[1]["content"] = user_prompt
        lc_messages = convert_openai_messages(prompt)
        response = ChatOpenAI(model=model_name, max_retries=1).invoke(lc_messages).content
        return response
