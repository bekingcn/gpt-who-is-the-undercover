# "Who is the Undercover" Game

Welcome to the "Who is the Undercover" game with a multi-agent AI application! This social deduction game combines langchain and langgraph to enable intelligent communication and decision-making among the players.

## Game Overview

In the "Who is the Undercover" game, a group of n players (where n is greater than or equal to 3) are divided into "innocent" players and "undercover" players. The "innocent" players receive the same word, while the "undercover" players receive a similar but different word. Each player can only make one statement per round to describe their word without directly revealing it, providing hints to their allies without giving away their identity to the undercover players. After each round of statements, players vote to eliminate who they suspect is the undercover player. The player with the most votes is eliminated, with ties leading to the next round. If only three players remain (including the undercover player), the undercover player wins; otherwise, the innocent players win.

## Multi-Agent Application

This multi-agent application utilizes [langchain](https://python.langchain.com/docs/get_started/introduction) and [langgraph](https://python.langchain.com/docs/langgraph/) to enable intelligent communication and decision-making among the players.
Together, these technologies enable the players to communicate effectively, make informed decisions, and uncover the identity of the undercover player.

## Installation

To install the game, you can clone this repository using Git. Once cloned, you can install the required dependencies by running the following command:

```sh
pip install -r requirements.txt
```

## How to Play

You can play the game in two ways:

### Using Streamlit

To start the game with a user interface using Streamlit, run the following command:

```sh
streamlit run st_main.py
```

### Using Command Line

Alternatively, you can run the game with command line by executing the following command:

```sh
python main.py
```

## Contributing

If you're interested in contributing to this project, please refer to the CONTRIBUTING.md file for guidelines on how to contribute.

## License

This project is licensed under the MIT License.

Feel free to customize and expand upon this README to provide more detailed information about your game and its usage. Let me know if you need further assistance!