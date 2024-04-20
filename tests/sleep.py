
# test with sleep

import time
from langgraph.graph import StateGraph
from langchain_core.pydantic_v1 import BaseModel
from typing import Annotated, Sequence, Dict
import operator

class AgentState(BaseModel):
    duration: int = 5
    messages: Annotated[Sequence[Dict], operator.add]


import time, random
def sleep(state):
    print("Enter sleep: ", state)
    if isinstance(state, AgentState):
        duration = state.duration
    d = random.uniform(0, duration)
    print(f"Sleeping for {d} seconds")
    time.sleep(d)
    return {"messages": [{"duration": duration, "sleep": d}]}

def route(duration):
    d = random.uniform(0, duration)
    print(f"Routing for {d} seconds")
    time.sleep(d)
    return {"duration": duration, "route": d}

class Main:
    def run(self):
        # Define a Langchain graph
        workflow = StateGraph(AgentState)

        # Add nodes for each agent
        workflow.add_node("sleeper-1", sleep)
        workflow.add_node("sleeper-2", sleep)
        workflow.add_node("sleeper-3", sleep)

        # Set up edges
        workflow.add_edge('sleeper-1', 'sleeper-2')
        workflow.add_edge('sleeper-2', 'sleeper-3')

        # set up start and end nodes
        workflow.set_entry_point("sleeper-1")
        workflow.set_finish_point("sleeper-3")

        # compile the graph
        chain = workflow.compile()

        # Execute the graph for each query in parallel
        # with ThreadPoolExecutor() as executor:
        #     parallel_results = list(executor.map(lambda q: chain.invoke({"query": q}), queries))

        result = chain.invoke({"duration": 5, "messages": []})

        return result


main = Main()
result = main.run()
print(result)