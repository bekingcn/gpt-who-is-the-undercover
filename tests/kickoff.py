from agents.kickoff import KickoffAgent
from base import GameState
# test Kickoff

import os
import time
from concurrent.futures import ThreadPoolExecutor
from langgraph.graph import Graph, StateGraph

class Main:
    def run(self):
        kickoff = KickoffAgent()
        # Define a Langchain graph
        workflow = StateGraph(GameState)

        # Add nodes for each agent
        workflow.add_node("kickoff", kickoff.run)

        # Set up edges

        # set up start and end nodes
        workflow.set_entry_point("kickoff")
        workflow.set_finish_point("kickoff")

        # compile the graph
        chain = workflow.compile()

        # Execute the graph for each query in parallel
        # with ThreadPoolExecutor() as executor:
        #     parallel_results = list(executor.map(lambda q: chain.invoke({"query": q}), queries))

        result = chain.invoke({"players_num": 7, 
                               "history": [],
                               "turn": 0,
                               "innocent_word": "",
                               "undercover_word": "",
                               "players_order": [],
                               "players_words": [],
                               "alive_status": [],
                               "statements": [],
                               "votes": [],
                               })
        return result
    
main = Main()
result = main.run()
print(result)