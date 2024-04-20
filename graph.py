from langgraph.graph import StateGraph, END

from agents.aiplayer import AIPlayerAgent
from agents.humanplayer import HumanPlayerAgent
from agents.kickoff import KickoffAgent
from agents.router import RouterAgent
from agents.base import GameState, PlayerData
from agents.base import TASK_NAME_END

def make_players_chain(
    workflow, 
    players_with_order: list[PlayerData], 
    callback=None, 
    user_callback=None, 
    with_human=False,
    rounds_history=False
    ):
    """
    Generate a chain of player nodes in a workflow based on the given order of players.

    :param workflow: The workflow to add the player nodes to.
    :param players_with_order: The players and their order in which players should be added to the workflow.
    :return: The starting player node and the ending player node of the chain.
    """
    players = []
    for p in players_with_order:
        # with a human player whose index is always 0
        # but we will re-order the players for their actions, for example: [3, 4, 0, 1, 2]
        # avoiding the human is the first player to take actions
        # TODO: for now, we are always name a human player randomly whatever the with_human setting
        # if this is set, this player will be interactable on the UI
        if with_human and p.is_human:
            agent = HumanPlayerAgent(p, callback=callback, user_callback=user_callback, rounds_history=rounds_history)
        else:
            agent = AIPlayerAgent(p, callback=callback, rounds_history=rounds_history)
        players.append((p, agent))
    player, agent = players[0]
    start_player = player.name
    last = start_player
    workflow.add_node(start_player, agent.run)
    for player, agent in players[1:]:
        workflow.add_node(player.name, agent.run)
        workflow.add_edge(last, player.name)
        last = player.name
    end_player = last
    return start_player, end_player

def router_continue(state):
    if state.current_task == TASK_NAME_END:
        return "end"
    else:
        return "continue"

from agents.gameconfig import GLOBAL_GAME_CONFIG, PLAYER_AGENTS_CONNECT_WITH_CHAIN, PLAYER_AGENTS_CONNECT_WITH_ROUTER
def graph(init_data: dict, callback=None, user_callback=None, with_human=None, rounds_history=None):
    if with_human is None:
        with_human = GLOBAL_GAME_CONFIG.with_human
    if rounds_history is None:
        rounds_history = GLOBAL_GAME_CONFIG.round_history

    workflow = StateGraph(GameState)

    kickoff = KickoffAgent(callback)
    router = RouterAgent(callback)

    # add nodes
    workflow.add_node("kickoff", kickoff.run)
    workflow.add_node("router", router.run)
    order = init_data.get("players_order")
    players = init_data.get("players")
    players_with_order = [players[p] for p in order]
    if GLOBAL_GAME_CONFIG.player_agents_connect_with == PLAYER_AGENTS_CONNECT_WITH_ROUTER:
        from agents.router import PlayerRouterAgent
        # the end_node (to router) is added as conditional edge in build_palyer_map
        player_router = PlayerRouterAgent(end_node="router", callback=callback)
        start_player, _ = player_router.build_routing(
            init_data,
            workflow,
            with_human=with_human,
            callback=callback,
            user_callback=user_callback,
            rounds_history=rounds_history,
        )
    elif GLOBAL_GAME_CONFIG.player_agents_connect_with == PLAYER_AGENTS_CONNECT_WITH_CHAIN:
        start_player, end_player = make_players_chain(
            workflow, 
            players_with_order, 
            callback=callback, 
            user_callback=user_callback, 
            with_human=with_human,
            rounds_history=rounds_history)
        workflow.add_edge(end_player, "router")
    else:
        raise NotImplementedError("Invalid player_agents_connect_with configuration")

    # add edges
    workflow.add_edge("kickoff", "router")

    workflow.add_conditional_edges(
        "router", 
        router_continue, 
        {
            "continue": start_player, 
            "end": END
        }
    )

    workflow.set_entry_point("kickoff")
    # workflow.set_finish_point("kickoff")
    
    result = workflow.compile()
    return result