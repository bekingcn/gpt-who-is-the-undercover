
REORDER_METHOD_SHUFFLE = "shuffle"
REORDER_METHOD_SHIFT = "shift"

REORDER_PLAYERS_NOTHING = None
REORDER_PLAYERS_EVERY_ROUND = "round"
REORDER_PLAYERS_EVERY_TASK = "task"

PLAYER_AGENTS_CONNECT_WITH_CHAIN = "chain"
PLAYER_AGENTS_CONNECT_WITH_ROUTER = "router"

# TODO: should we add this as parameter for calls?
# for now, we support it as global config
class GameConfig:
    def __init__(
        self,
        players_num: int = 3,
        with_humans: int = 1,
        round_history: bool = False,
        callback=None,
        user_callback=None,
        reorder_players=REORDER_PLAYERS_NOTHING,
        order_players_by=REORDER_METHOD_SHUFFLE,
        player_agents_connect_with=PLAYER_AGENTS_CONNECT_WITH_ROUTER,   # chain or router
        human_input_timeout = 60
    ):
        self.players_num = players_num
        self.with_humans = with_humans
        self.round_history = round_history
        self.callback = callback
        self.user_callback = user_callback
        # reorder players every round or every task: None, "round", "task"
        # this is supputed by PlayerRouterAgent
        self.reorder_palyers = reorder_players
        self.order_players_by = order_players_by   # or shift
        self.player_agents_connect_with = player_agents_connect_with
        self.human_input_timeout = human_input_timeout

    
    @property
    def with_human(self) -> bool:
        return self.with_humans>0

GLOBAL_GAME_CONFIG = GameConfig(
    players_num=3, 
    with_humans=0, 
    round_history=False,
    reorder_players=REORDER_PLAYERS_NOTHING,
    order_players_by=REORDER_METHOD_SHUFFLE,
    player_agents_connect_with=PLAYER_AGENTS_CONNECT_WITH_ROUTER,
    human_input_timeout = 60
)
