from .base import GameState, PlayerData
from .base import TASK_NAME_END, TASK_NAME_KICKOFF, TASK_NAME_STATEMENT, TASK_NAME_VOTE, PLAYER_INDEX_ROUTER
from .base import ROUTER_EVENT_NAME_GAME_END, ROUTER_EVENT_NAME_ROUND_END, ROUTER_EVENT_NAME_KICKOFF, ROUTER_EVENT_NAME_STATEMENT_END, ROUTER_EVENT_NAME_VOTE_END
from .base import FINAL_RESULT_INNOCENT_WIN, FINAL_RESULT_UNDERCOVER_WIN, FINAL_RESULT_QUIT_WRONG_VOTE
from .gameconfig import REORDER_PLAYERS_EVERY_ROUND, REORDER_PLAYERS_EVERY_TASK, REORDER_PLAYERS_NOTHING

from .aiplayer import AIPlayerAgent
from .humanplayer import HumanPlayerAgent

class RouterAgent:
    def __init__(self, callback=None):
        self.callback = callback or self._callback
    
    def _callback(self, player_index, task, task_output, state=None):
        print(f"Router: {task_output}")

    def run(self, state: GameState):
        # TODO: more check with state
        # start statement
        if state.current_task == TASK_NAME_KICKOFF:
            task_output = {
                "event": ROUTER_EVENT_NAME_KICKOFF,
                "current_task": TASK_NAME_STATEMENT,
                "turn": 1
            }
            self.callback(PLAYER_INDEX_ROUTER, TASK_NAME_KICKOFF, task_output, state)
            reuslt = {
                "current_task": TASK_NAME_STATEMENT,
                "turn": 1
            }
            return reuslt
        # from statement to vote
        if state.current_task == TASK_NAME_STATEMENT:
            task_output = {
                "event": ROUTER_EVENT_NAME_STATEMENT_END,
                "current_task": TASK_NAME_STATEMENT,
                "turn": state.turn,
            }
            self.callback(PLAYER_INDEX_ROUTER, TASK_NAME_STATEMENT, task_output, state)
            reuslt = {
                "current_task": TASK_NAME_VOTE
            }
            return reuslt
        # finished voting
        if state.current_task == TASK_NAME_VOTE:
            reuslt = self.check_turn_result(state)
            task_output = {"event": ROUTER_EVENT_NAME_VOTE_END, **reuslt}
            self.callback(PLAYER_INDEX_ROUTER, TASK_NAME_VOTE, reuslt, state)
            return reuslt
        raise Exception("Invalid state")
    
    def alive_players_num(self, state: GameState):
        return state.alive_status.count(True)
    
    def check_turn_result(self, state: GameState):
        votes = state.votes
        # count the votes with the same number
        votes_by_number = {}
        for vote in votes:
            # filter with players who are not alive
            if vote == -1:
                continue
            if vote in votes_by_number:
                votes_by_number[vote] += 1
            else:
                votes_by_number[vote] = 1
        # get the number and votes with the max number
        # TODO: if the votes are equal, get the first one for now
        # the player index who is voted as undercover
        out_player_index = max(votes_by_number, key=votes_by_number.get)
        out_player_votes = votes_by_number[out_player_index]
        out_player_word = state.players_words[out_player_index]
        task_output = {
            "event": ROUTER_EVENT_NAME_VOTE_END, 
            "player_out_of_game": out_player_index, 
            "votes": out_player_votes
            }
        self.callback(PLAYER_INDEX_ROUTER, TASK_NAME_VOTE, task_output, state)
        if not state.is_alive(out_player_index):
            task_output = {
                "event": ROUTER_EVENT_NAME_GAME_END,
                "final_result": FINAL_RESULT_QUIT_WRONG_VOTE,
                "alive_status": state.alive_status,
            }
            self.callback(PLAYER_INDEX_ROUTER, TASK_NAME_END, task_output, state)
            return {
                "current_task": TASK_NAME_END,
                "final_result": FINAL_RESULT_QUIT_WRONG_VOTE,
            }

        new_alive_status = state.alive_status.copy()
        new_alive_status[out_player_index] = False
        # end game with undercover was voted
        if out_player_word == state.undercover_word:
            task_output = {
                "event": ROUTER_EVENT_NAME_GAME_END, 
                "final_result": FINAL_RESULT_INNOCENT_WIN,
                "alive_status": new_alive_status,
                }
            self.callback(PLAYER_INDEX_ROUTER, TASK_NAME_VOTE, task_output, state)
            return {
                "current_task": TASK_NAME_END,
                "final_result": FINAL_RESULT_INNOCENT_WIN,
                "alive_status": new_alive_status,
                "history": [self.generate_turn_result(state, out_player_index)],
            }
        # end game with reach the last 3 players including the undercover
        elif new_alive_status.count(True) == 3:
            # reach the last 3 players with new alive status
            task_output = {
                "event": ROUTER_EVENT_NAME_GAME_END, 
                "final_result": FINAL_RESULT_UNDERCOVER_WIN,
                "alive_status": new_alive_status,
                }
            self.callback(PLAYER_INDEX_ROUTER, TASK_NAME_VOTE, task_output, state)
            return {
                "current_task": TASK_NAME_END,
                "final_result": FINAL_RESULT_UNDERCOVER_WIN,
                "alive_status": new_alive_status,
                "history": [self.generate_turn_result(state, out_player_index)],
            }
        # round end, start new round by init new state data 
        else:
            task_output = {"event": ROUTER_EVENT_NAME_ROUND_END, "round": state.turn, "alive_status": new_alive_status}
            self.callback(PLAYER_INDEX_ROUTER, TASK_NAME_VOTE, task_output, state)
            return {
                "alive_status": new_alive_status,
                "current_task": TASK_NAME_STATEMENT,    # start new round with statement stage
                "turn": state.turn + 1,
                # clear statements and votes
                "statements": [""] * state.players_num,
                "votes": [-1] * state.players_num,
                # update players order because of new alive status are changed
                "players_order": state._order_players_by(order_type="statement", new_alive_status=new_alive_status),
                # append the turn result to the history
                "history": [self.generate_turn_result(state, out_player_index)],
            }
        
    def generate_turn_result(self, state: GameState, out_player_index: int):
        return {
            "statements": state.statements,
            "votes": state.votes,
            "out": out_player_index,
            "turn": state.turn
        }



# TODO: move this outside
from langgraph.graph import StateGraph
class PlayerRouterAgent:
    # reorder players every round or every task: None, "round", "task"
    def __init__(self, end_node: str=None, reorder_players=REORDER_PLAYERS_NOTHING, node_name = None, callback=None):
        self.end_node = end_node
        self.node_name = node_name or "player_router"
        self.callback = callback or self._callback

        self.reorder_palyers_every_round = reorder_players == REORDER_PLAYERS_EVERY_ROUND
        self.reorder_palyers_every_task = reorder_players == REORDER_PLAYERS_EVERY_TASK
    
    def _callback(self, player_index, task, task_output, state=None):
        print(f"Player Router: {task_output}")
        
    def run(self, state: GameState):
        order = state.players_order
        # TODO: move this into RouterAgent?
        # force re-order players every round or every task
        from .base import ROUTER_EVENT_NAME_TASK_START, ROUTER_EVENT_NAME_ROUND_START
        if state.next_player_index == -1:
            # this is the start of a round
            if state.current_task == TASK_NAME_STATEMENT and self.reorder_palyers_every_round:
                order = state._create_order(order)
                task_output = {"event": ROUTER_EVENT_NAME_ROUND_START, "round": state.turn, "players_order": order}
                self.callback(PLAYER_INDEX_ROUTER, state.current_task, task_output, state)
            elif self.reorder_palyers_every_task:
                # this is the start of a task
                order = state._create_order(order)
                task_output = {"event": ROUTER_EVENT_NAME_TASK_START, "task": state.current_task, "round": state.turn, "players_order": order}
                self.callback(PLAYER_INDEX_ROUTER, state.current_task, task_output, state)
        # check current task and current player
        # find next player or end this task stage
        if state.current_task == TASK_NAME_STATEMENT:
            next = self._next_player(state.next_player_index, order, state.alive_status)
        elif state.current_task == TASK_NAME_VOTE:
            next = self._next_player(state.next_player_index, order, state.alive_status)
        elif state.current_task == TASK_NAME_END:
            next = self._next_player(state.next_player_index, order, state.alive_status)
        else:
            raise NotImplementedError("Invalid current task")
        # update the players order at the same time
        return {"next_player_index": next, "players_order": order}
    
    # find out the next alive player
    def _next_player(self, current: int, lst: list[int], alive_status: list[bool]) -> int:
        # task stage start with -1
        if current == -1:
            return lst[0]
        start = lst.index(current)
        # loop from next player to the end
        for i in range(start+1, len(lst)):
            if alive_status[lst[i]]:
                return lst[i]
        # end this task stage with -1
        return -1
    
    # for conditional edge check in graph
    def to_player(self, state: GameState):
        if state.next_player_index == -1:
            return "task_end"
        else:
            return state.players[state.next_player_index].name
    
    def build_palyer_map(self, players: list[PlayerData]):
        player_map = {p.name: p.name for p in players}
        player_map["task_end"] = self.end_node
        return player_map
    
    def build_routing(self, init_data: dict, workflow: StateGraph, with_human: bool, callback, user_callback, rounds_history):
        # self as player router        
        workflow.add_node(self.node_name, self.run)
        players = init_data["players"]
        for p in players:
            if with_human and p.is_human:
                agent = HumanPlayerAgent(p, callback=callback, user_callback=user_callback, rounds_history=rounds_history)
            else:
                agent = AIPlayerAgent(p, callback=callback, rounds_history=rounds_history)
            workflow.add_node(p.name, agent.run)
            workflow.add_edge(p.name, self.node_name)
        workflow.add_conditional_edges(
            self.node_name,
            self.to_player,
            self.build_palyer_map(players),
        )
        return self.node_name, self.node_name