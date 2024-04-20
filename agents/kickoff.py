import random, json
from langchain.adapters.openai import convert_openai_messages
from langchain_openai import ChatOpenAI

from .prompts import PROMPT_KICKOFF
from .base import TASK_NAME_KICKOFF

model_name = "gpt-3.5-turbo"

# Agent that kicks off the game
# the agent will use the state to kick off the game
# responsibilities:
# - provide the innocent word and the uncercover word
# - provide the order of the players
# - send a word to each player
class KickoffAgent:
    def __init__(self, callback=None):
        self.callback = callback or self._callback
        
    def _callback(self, player_index, task, task_output, state=None):
        print(f"kickoff words: {task_output.get('innocent_word')}, {task_output.get('undercover_word')}")
        print(f"kickoff players words: {task_output.get('players_words')}")
        print (f"kickoff players' order: {task_output.get('players_order')}")
    
    def run(self, state):
        self.state = state
        words = self._create_words()
        players_words = self._send_words_to_players(words[0], words[1], self.state.players_num)
        task_output = {
            "innocent_word": words[0], 
            "undercover_word": words[1],
            "players_words": players_words,
            "order": state.players_order,
            "turn": 1,
        }
        self.callback(-1, TASK_NAME_KICKOFF, task_output, state)
        return {
            "players_num": state.players_num,
            "innocent_word": words[0],
            "undercover_word": words[1],
            "players_words": players_words,
            "players_order": state.players_order,
            "turn": 1,
            "current_task": "kickoff",
            "history": [],
            "final_result": "",
        }
    
    def _create_words(self):
        generated = self.generate()
        return generated.get("innocent_word"), generated.get("undercover_word")

    def _send_words_to_players(self, innocent_word, undercover_word, players_num):
        undercover = random.randint(0, players_num-1)
        words = [undercover_word if undercover == i else innocent_word for i in range(players_num)]
        return words
    
    def generate(self):
        lc_messages = convert_openai_messages(PROMPT_KICKOFF) # (prompt)
        response = ChatOpenAI(model=model_name, max_retries=1).invoke(lc_messages).content
        response = response.strip("```").strip("json").strip("\"'")
        return json.loads(response)