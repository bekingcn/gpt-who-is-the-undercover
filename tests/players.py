from sample_data import sample_data_3_palyer_for_votes
from agents.base import GameState
from agents.aiplayer import AIPlayerAgent
# test Players

from langgraph.graph import Graph, StateGraph
init_data = sample_data_3_palyer_for_votes
state = GameState(**init_data)

players = []
for i in state.players_order:
    player = AIPlayerAgent(i)
    players.append((i, player))


workflow = StateGraph(GameState)
i, p = players[0]
last = f"player_{i}"
workflow.add_node(f"player_{i}", p.run)
workflow.set_entry_point(last)
for i, p in players[1:]:
    workflow.add_node(f"player_{i}", p.run)
    workflow.add_edge(last, f"player_{i}")
    last = f"player_{i}"

workflow.set_finish_point(last)
retuslt = workflow.compile().invoke(init_data)

print(workflow.schema)