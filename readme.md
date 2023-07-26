# Quiz Bot

This is the code for the quiz bot, a fun game bot designed to be used with Discord to manage card games with challenges. 

## Features

- The bot reads in card prompts from text files, which can easily be customized and extended.
Each card should be on a new line and each text file is a 'pack' of cards that can be included.
Cards prefixed a * are worth no points, and usually just uesd to mock a player. 
- Players vote on whether they think the current player has passed or failed their card prompt. If somebody 'fails' the card is returned to the pack.
- The game keeps track of scores automatically, end the game with `!eg` to view scores

## Commands

- `!vote [pass/fail]` or `!v [pass/fail]`: Vote on whether you think the current player will pass or fail.
- `!start-game` or `!sg`: Start a new game.
- `!select-channel [number]` or `!sc [number]`: Select the voice channel for the game.
- `!use [expansion numbers]`: Select which expansions to use for the current game.
- `!end-game` or `!eg`: End the current game.
- `!shuffle`: Shuffle the current deck.

## Installation

1. Clone this repository.
2. Install the necessary packages by running `pip install -r requirements.txt`.
3. Run `python game.py`.

Remember to replace `'key'` in the `bot.run('key')` command with your actual Discord bot token.

## Contributing

Pull requests are always welcome.

## License

[MIT](https://choosealicense.com/licenses/mit/)
