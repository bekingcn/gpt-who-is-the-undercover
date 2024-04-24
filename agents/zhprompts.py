PROMPT_GEME_DESC = """
游戏：谁是卧底

选择一对词语，其中一个单词给平民玩家，另一个给唯一的卧底玩家。
分配角色：平民玩家收到相同的单词，而卧底玩家收到不同的词语。
玩家轮流描述他们的词语，但不能过于直白的揭示。
玩家根据他们的陈述来识别卧底玩家。
得票最多的玩家被淘汰，进入下一轮，直到卧底被淘汰或只剩下三个玩家。
"""

PROMPT_KICKOFF_PERSONAL = """
你是游戏的主持人，提供游戏的词语
"""

PROMPT_KICKOFF_RULES = """
词语示例：
{word_pair_examples}

参照上面的示例，提供一对额外的有趣的单词。
返回格式：
{{
    "innocent_word": "innocent word",
    "undercover_word": "undercover word"
}}
仅返回JSON，不要返回其它内容。
"""

PROMPT_KICKOFF = [
    {
        "role": "system",
        "content": f"""
{PROMPT_KICKOFF_PERSONAL}
{PROMPT_GEME_DESC}
"""},
    {
        "role": "user",
        "content": PROMPT_KICKOFF_RULES
    }
]


PROMPT_PLAYER_PERSONAL = f"""
你是"谁是卧底"游戏的高级玩家。
"""

PRMMPT_PALYER_STATEMENT_ROUNDS = """
本轮已完成的陈述：

{round_history_statements}
"""

PROMPT_PLAYER_STATEMENT_RULES = """
基于前面的其他玩家的陈述思考策略，策略建议：

平民玩家：
提供一个微妙的陈述，但不要太明显。
观察其他玩家的描述，寻找不一致或可疑行为。

卧底玩家：
考虑如何合理描述你的单词，以便混淆其他玩家的判断。
尝试找出其他玩家的词语。

不确定的玩家：
保持中立的立场，观察反应，评估情况。
使用你的陈述来评估其他玩家的回应，但不泄露你的身份。
"""

PROMPT_PLAYER_STATEMENT = [
    {
        "role": "system", 
        "content": f"""
{PROMPT_PLAYER_PERSONAL}
{PROMPT_GEME_DESC}

{PROMPT_PLAYER_STATEMENT_RULES}
"""},
    {
        "role": "user", 
        "content": ""
    }
]

PRMMPT_PALYER_VOTING_ROUNDS = """
本轮所有的陈述：

{round_history_statements}
"""
PROMPT_PLAYER_VOTING_RULES = """
首先通过所有陈述分析自己的角色和其他玩家的橘色，然后基于认定的角色进行投票。

平民角色
分析其他玩家的陈述，寻找任何不一致或可疑的卧底玩家。

卧底玩家的投票策略：
找出最容易被投出局的玩家，避免自己票数过高出局。

不确定玩家的投票策略：
跟着感觉走:)。
"""

PLAYER_VOTING_JSON_FORMAT = """{
    "vote": 卧底玩家的number,
    "reason": "为什么该玩家是卧底的一句话原因（中文）",
    "role": "你是什么角色，平民还是卧底？"
}"""

PROMPT_PLAYER_VOTING = [
    {
        "role": "system", 
        "content": f"""
{PROMPT_PLAYER_PERSONAL}
{PROMPT_GEME_DESC}

{PROMPT_PLAYER_VOTING_RULES}
"""},
    {
        "role": "user", 
        "content": ""
    }
]

INIT_WORD_PAIR_EXAMPLES = [
    ["电动车", "摩托车"],
    ["班主任", "辅导员"],
    ["公交", "地铁"],
    ["男朋友", "前男友"],
    ["魔术师", "魔法师"],
    ["甄子丹", "李连杰"],
]


def format_player_statement_prompt(turn, history, word, player_index):
    user_prompt = f"""
第 {turn} 轮
本轮已完成的陈述：

{history}

你是玩家 {player_index}；
你的词语 {word}；
对你的词语做出陈述，要求：一句话；使用中文；不要直接说出这个词语；不要重复前面任何人的陈述
"""
    prompt = PROMPT_PLAYER_STATEMENT.copy()
    prompt[1]["content"] = user_prompt
    return prompt

def format_player_voting_prompt(turn, history, word, player_index):
    user_prompt = f"""
第 {turn} 轮
本轮已完成的陈述：

{history}

你是玩家 {player_index}；
你的词语 {word}；
投票给你认为是卧底玩家的player index.

返回格式：
{PLAYER_VOTING_JSON_FORMAT}
仅返回JSON，不要返回其它内容。
"""
    prompt = PROMPT_PLAYER_VOTING.copy()
    prompt[1]["content"] = user_prompt
    return prompt