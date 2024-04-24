STATEMENT_PROMPT_SYSTEM = """


In the "Who is the undercover" game, players take turns describing a word without revealing it. 
There are innocent players who receive the same word, and an undercover player who receives a different word. 
The goal is to identify the undercover player by analyzing the statements. 
Strategies for the statement stage include: 
- innocent players providing subtle hints, 
- undercover players blending in, 
- and uncertain players using ambiguous statements. 
The game continues until the undercover player is eliminated or only three players remain. 
The player with the most votes is eliminated in each round.


"""

STATEMENT_PROMPT_USER = """

"Round {round_number}: 
Finished statements:
{previous_statements}. 

Your word: {player_word}, index: {player_index}. 
Make a unique statement without repeating any previous statements."

"""

VOTE_PROMPT_SYSTEM = """


You are a perfect player of the "Who is the undercover" game.


Game: Who is the Undercover
- Select word pairs where one word is innocent and the other is undercover.
- Assign roles: innocent players receive the same word, while the undercover player receives a different word.
- Players take turns describing their word without revealing it.
- Players identify the undercover player based on their statements.
- The player with the most votes is eliminated, with ties leading to the next round, until the undercover player is eliminated or only three players remain.



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

VOTE_PROMPT_USER = """

"Round {round_number}: 
Finished statements:
{previous_statements}. 

Your word: {player_word}, index: {player_index}. 
Voting and reasoning in the format of your return:
{
    "vote": [the index number of the undercover player], 
    "reason": "an short reason why the player is undercover",
    "role": "what's yout role, innocent or undercover"
}
Please return nothing but the JSON.
"""

KICKOFF_PROMPT_SYSTEM = """

In the game "Who is the Undercover," choose word pairs with one innocent and one undercover word. Assign roles accordingly.

Players describe their words without revealing them. 
Identify the undercover player based on statements. 
Eliminate the player with the most votes, with ties leading to the next round. 
Keep playing until the undercover player is caught or only three players remain.

"""

KICKOFF_PROMPT_USER = """

You are kicking off the game. 
Select word pairs with subtle connections, making it challenging for the undercover player. 

Maintain distinct innocent words and specific undercover words. 

{"innocent_word": "Cupcake", "undercover_word": "Muffin"}
"""

