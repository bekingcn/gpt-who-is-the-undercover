

PROMPT_GEME_DESC = """
Game: Who is the Undercover
- Select word pairs where one word is innocent and the other is undercover.
- Assign roles: innocent players receive the same word, while the undercover player receives a different word.
- Players take turns describing their word without revealing it.
- Players identify the undercover player based on their statements.
- The player with the most votes is eliminated, with ties leading to the next round, until the undercover player is eliminated or only three players remain.
"""
BAK1 = """
Rules:
Among n (where n is greater than or equal to 3) players, 
n-1 players receive the same word or phrase (could be an object name, fictional character, or a person's name), 
while the remaining player receives a similar but different word.
Each player can only say one sentence to describe the word they received (without directly revealing the word), 
trying to hint to their teammates without giving away to the undercover player.
After each round of descriptions, all n players vote on who they suspect is the undercover player.
The player with the most votes is eliminated;
in case of a tie, the game proceeds to the next round.
If there are only three players left (including the undercover), the undercover wins; otherwise, the other players win.
"""

PROMPT_KICKOFF_PERSONAL = """
As a moderator, you are creating an exciting and strategic gameplay experience for all participants in the game "Who is the Undercover."
"""

PROMPT_KICKOFF_RULES = """
You should consider the following suggestions:
- Choose word/phrase pairs that have subtle connections or similarities, making it challenging for the undercover player to differentiate.
- Ensure that the innocent words are distinct but not too obvious, while the undercover words are slightly more specific or unique.

Here are the sample word/phrase pairs for the game:
Ice Cream (innocent) and Sorbet (undercover)
The Eiffel Tower (innocent) and The Great Wall of China (undercover)
Books (innocent) and Magazines (undercover)
Beach (innocent) and Desert (undercover)
Guitar (innocent) and Banjo (undercover)
Mountain (innocent) and Volcano (undercover)
Sunflower (innocent) and Rose (undercover)
Bicycle (innocent) and Unicycle (undercover)
Lemonade (innocent) and Mojito (undercover)

By following these samples and providing extra engaging word pairs.
Here is the format of your return:
{
    "innocent_word": "innocent word",
    "undercover_word": "undercover word"
}
Please return nothing but the JSON.
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
You are a perfect player of the "Who is the undercover" game.
"""

PRMMPT_PALYER_STATEMENT_ROUNDS = """
Here are the statements before the current round:

{round_history_statements}
"""

PROMPT_PLAYER_STATEMENT_RULES = """
Here are the strategies for the statement stage based on the different player roles:
Innocent Player:
- Provide a subtle hint about your word without revealing it directly.
- Craft a statement that offers a clue without making it too obvious.
- Pay attention to the descriptions of others and look for inconsistencies or suspicious behavior.

Undercover Player:
- Create a vague description that aligns with innocent players' words but sets you apart.
- Avoid being too specific or standing out with your statement.
- Blend in with innocent players while planting doubt among them subtly.

Uncertain Player:
- Keep your statement ambiguous and open to interpretation.
- Maintain a neutral position to observe reactions and assess the situation.
- Use your statement to gauge the responses of other players without giving away your role.
"""

PRMMPT_PALYER_VOTING_ROUNDS = """
Here are the statements before the current round:

{round_history_statements}
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


PROMPT_PLAYER_VOTING_RULES = """
Here are the strategies for the voting stage based on the different player roles::
Innocent Player:
- Assess the statements made by others and look for any inconsistencies or suspicious behavior.
- Consider the voting patterns and try to identify any potential undercover players.
- Use critical thinking and deductive reasoning to make an informed decision during the voting process.

Undercover Player:
- Observe the voting patterns and try to gauge the suspicions of the innocent players.
- Adjust your voting strategy based on the dynamics of the group and the behavior of the other players.
- Avoid drawing attention to yourself during the voting stage.

Uncertain Player:
- Pay close attention to the voting patterns and the behavior of the other players.
- Use the voting stage to gather additional information and assess the dynamics of the group.
- Make a calculated decision based on the information gathered during the statement stage.
"""


PLAYER_VOTING_JSON_FORMAT = """{
    "vote": [the index number of the undercover player], 
    "reason": "the reason why the player is undercover",
    "role": "what's yout role, innocent or undercover"}"""

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

