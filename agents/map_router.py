from langgraph.graph import StateGraph
from typing import TypedDict, Annotated, Union
from langchain_core.runnables import RunnableConfig

# Fow now this is just an idea, because it requires a Complex State structure 
# with the state check as below:

"""
if any(isinstance(c, BinaryOperatorAggregate) for c in self.channels.values()):
    self.support_multiple_edges = True
"""
class MapRouterAgent:
    def __init__(self, node_name=None, run_func=None):
        self.node_name = node_name or "map_router"
        self.run_func = run_func or self._run
    
    def _run(self, state):
        # TODO
        return None
    
    def run(self, state):
        return self.run_func(state)
    
    @classmethod
    def route_nodes(
        cls, 
        workflow: StateGraph, 
        start_name: str, 
        end_nodes: list[str], 
        run_func=None):
        router = MapRouterAgent(node_name=start_name, run_func=run_func)
        workflow.add_node(router.node_name, router.run)
        for node in end_nodes:
            # workflow.add_node(node, c)
            workflow.add_edge(router.node_name, node)
            
        return workflow




from typing import Sequence, Tuple, Set
import operator
from langchain_core.pydantic_v1 import BaseModel
class PlayerData(BaseModel):
    index: int
    name: str
    is_human: bool
    statement_order: int
    vote_order: int
    discussion_order: int

# an alternative way to make all properties be a BinaryOperatorAggregate
class GameState(BaseModel):
    # ---
    # these properties will be initialized from kickoff and not changed any more
    # user input
    players_num: Annotated[Sequence[int], operator.add]
    # init state
    players: Annotated[Sequence[PlayerData], operator.add]
    # kickoff fills the words
    innocent_word: Annotated[Sequence[str], operator.add]
    undercover_word: Annotated[Sequence[str], operator.add]
    # by player index
    players_words: Annotated[Sequence[str], operator.add]


    # ---
    # below properties will be filled in one or more agents
    # so we use the latest one
    # judge and fills by router output
    # TODO: not needed, players in current round and order
    players_order: Annotated[Sequence[int], operator.add]
    alive_status: Annotated[Sequence[bool], operator.add]
    turn: Annotated[Sequence[int], operator.add]
    current_task: Annotated[Sequence[str], operator.add]
    final_result: Annotated[Sequence[str], operator.add]    # only once at final
    
    # fill by player index
    statements: Annotated[Sequence[Set[int, int, str]], operator.add]   # round/turn, player index, statement
    votes: Annotated[Sequence[Set[int, int, int]], operator.add]   # round/turn, player index, vote to index
    
    # fill by player router
    # next player index with current task, or -1 if there is no next player
    next_player_index: Annotated[Sequence[int], operator.add]
    
    @property
    def current_players_order(self) -> Sequence[int]:
        return self.players_order[-1]
    
    @property
    def current_alive_status(self) -> Sequence[bool]:
        return self.alive_status[-1]
    
    @property
    def current_turn(self) -> int:
        return self.turn[-1]
    
    @property
    def current_task_name(self) -> str:
        return self.current_task[-1]
    
    @property
    def current_final_result(self) -> str:
        return self.final_result[-1]
    
    @property
    def current_round_statements(self) -> list[Set[int, int, str]]:
        return [ s for s in self.statements if s[0] == self.current_turn ]
    
    @property
    def current_round_votes(self) -> list[Set[int, int, int]]:
        return [ s for s in self.votes if s[0] == self.current_turn ]


## ----
# Tests

from typing import Sequence, Tuple
import operator

# have to make all properties be a BinaryOperatorAggregate and annotated
class MyState(TypedDict):
    task: Annotated[Sequence[str], operator.add]
    sum: Annotated[Sequence[int], operator.add]
    values: Annotated[Sequence[Tuple[str, int]], operator.add]


init_data = {
    "task": [],
    "sum": [],
    "values": [],
}

def create_func(name, index):
    def my_func(state: MyState):
        import time, random
        time.sleep(5)
        v = random.randint(0, 10)
        return {"values": [(name, v)]}
    return my_func
    
def sum_func(state: MyState):
    ret = sum([v[1] for v in state["values"]])
    print(f"Sum: {ret}")
    return {"sum": [ret]}

def test_map_router():    
    workflow = StateGraph(MyState)
    func0 = create_func("func0", 0)
    func1 = create_func("func1", 1)
    func2 = create_func("func2", 2)
    
    workflow.add_node("func0", func0)
    workflow.add_node("func1", func1)
    workflow.add_node("func2", func2)
    
    workflow = MapRouterAgent.route_nodes(workflow, "map_router", ["func0", "func1", "func2"])
    
    workflow.add_node("sum_all", sum_func)
    workflow.add_edge("func0", "sum_all")
    workflow.add_edge("func1", "sum_all")
    workflow.add_edge("func2", "sum_all")
    
    workflow.set_entry_point("map_router")
    workflow.set_finish_point("sum_all")
    config = RunnableConfig(recursion_limit=120)
    
    workflow = workflow.compile(debug=True)
    result = workflow.invoke(init_data, config=config)

    print(result)

if __name__ == "__main__":
    test_map_router()