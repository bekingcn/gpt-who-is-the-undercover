import random, json
from langchain.adapters.openai import convert_openai_messages
from langchain_openai import ChatOpenAI

from .base import TASK_NAME_KICKOFF
from .gameconfig import GLOBAL_LANGUAGE, update_word_pair_examples
if GLOBAL_LANGUAGE == "zh":
    from .zhprompts import PROMPT_KICKOFF, PROMPT_KICKOFF_RULES
else:
    from .prompts import PROMPT_KICKOFF, PROMPT_KICKOFF_RULES

model_name = "gpt-3.5-turbo"

# Agent that kicks off the game
# the agent will use the state to kick off the game
# responsibilities:
# - provide the innocent word and the uncercover word
# - provide the order of the players
# - send a word to each player
class KickoffAgent:
    def __init__(self, word_pair_examples=[], callback=None):
        self.callback = callback or self._callback
        self.word_pair_examples = word_pair_examples
        
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
        # replace the user content here, with the updated word pair examples
        user_prompt = PROMPT_KICKOFF_RULES.format(word_pair_examples=update_word_pair_examples(self.word_pair_examples))
        kickoff_prompt = PROMPT_KICKOFF.copy()
        kickoff_prompt[1]["content"] = user_prompt
        lc_messages = convert_openai_messages(kickoff_prompt)
        response = ChatOpenAI(model=model_name, max_retries=1).invoke(lc_messages).content
        response = response.strip("```").strip("json").strip("\"'")
        return json.loads(response)
    
## ----
## test

def test_generate():
    word_pair_examples = [
        ["Piano", "Accordion"],
        ["Butterfly", "Moth"],
        ["Books", "Magazines"],
        ["Beach", "Desert"],
        ["Ice Cream", "Sorbet"],
        ["The Eiffel Tower", "The Great Wall of China"],
    ]
    
    kickoff = KickoffAgent(word_pair_examples=word_pair_examples)
    result = kickoff.generate()
    print(result)
    
if __name__ == "__main__":
    test_generate()