import discord
import random
import os
import asyncio
from discord.ext import commands
from difflib import get_close_matches

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
bot = commands.Bot(command_prefix='!', intents=intents)

votes = {}
cards = []
expansions = {}
game_interrupt = asyncio.Event()
scores = {}
voice_channel = None

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.event
async def on_message(message):
    if message.content.startswith('!'):
        print(f'Command received: {message.content}')
    await bot.process_commands(message)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        cmd = ctx.message.content.split(" ")[0][1:]  # get the command
        matches = get_close_matches(cmd, bot.all_commands.keys())
        if matches:
            await ctx.send(f"Command {cmd} not found, did you mean {matches[0]}?")
        else:
            await ctx.send(f"Command {cmd} not found, and I don't know what you meant. Please check your command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"You're missing some arguments. Please check your command.")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"That command is on cooldown, please try again in {error.retry_after:.2f} seconds.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send(f"You don't have the necessary permissions to use this command.")
    elif isinstance(error, commands.CheckFailure):
        await ctx.send(f"You're not allowed to use this command.")
    else:
        # if the error is not recognized (it's not in the errors we check for)
        await ctx.send(f"An error occurred: {str(error)}")

def load_expansion(expansion):
    expansion_dir = 'expansions'
    expansion_file = os.path.join(expansion_dir, expansion + '.txt')
    if os.path.exists(expansion_file):
        with open(expansion_file, 'r') as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    else:
        return []

@bot.command(name='vote', aliases=['v'])
async def vote(ctx, vote: str):
    global game_interrupt
    if vote not in ['pass', 'fail']:
        await ctx.send(f'Invalid vote. Please use: `!vote pass` or `!vote fail`')
        return

    # prevent the current player from voting
    if ctx.author.id == current_player.id:
        return

    votes[ctx.author.id] = vote
    await ctx.send(f'{ctx.author.mention}, your vote has been recorded.')

    # check if a majority has been reached, if so, interrupt the sleep in start_game
    players_count = len([m for m in ctx.guild.members if not m.bot and m.voice and m.voice.channel.name == voice_channel]) - 1
    if len(votes) > players_count // 2:
        game_interrupt.set()

async def ask_for_expansions(ctx):
    global expansions
    expansions = {i: filename[:-4] for i, filename in enumerate(os.listdir('expansions'), start=1) if filename.endswith('.txt')}
    await ctx.send('Here are the available expansions:\n' + '\n'.join(f'{i}. {expansion}' for i, expansion in expansions.items()) +
                   '\n\nTo select expansions to use, please respond with the `!use` command followed by the numbers of the expansions you want, separated by commas. ' +
                   'For example, to select the first, second and fifth expansions, type `!use 1,2,5`.')

@bot.command(name='start-game', aliases=['sg'])
async def start_game(ctx):
    global voice_channel
    if voice_channel is None:
        populated_channels = {i: channel.name for i, channel in enumerate((c for c in ctx.guild.voice_channels if len(c.members) > 0), start=1)}
        await ctx.send('Here are the available voice channels:\n' + '\n'.join(f'{i}. {channel}' for i, channel in populated_channels.items()) +
                    '\n\nTo select the voice channel, please respond with the `!select-channel` or `!sc` command followed by the number of the channel. ' +
                    'For example, to select the first voice channel, type `!select-channel 1` or `!sc 1`.')

@bot.command(name='select-channel', aliases=['sc'])
async def select_channel(ctx, index: int):
    global voice_channel
    populated_channels = [channel for channel in ctx.guild.voice_channels if len(channel.members) > 0]
    if 1 <= index <= len(populated_channels):
        voice_channel = populated_channels[index - 1]
        await ask_for_expansions(ctx)
    else:
        await ctx.send('Invalid voice channel selection. Please select a valid number using `!select-channel` or `!sc`.')

@bot.command(name='use')
async def use(ctx, indices: str):
    global cards, game_interrupt
    indices = [i for i in indices.replace(" ", "").split(',') if i]
    for index in map(int, indices):
        if index in expansions:
            cards += load_expansion(expansions[index])
    random.shuffle(cards)
    cards = cards[:60]  # cut to 60

    if not cards:
        await ctx.send('No cards available.')
        return

    await ctx.send('Expansions loaded. Starting game now...')
    await run_game(ctx)


async def run_game(ctx):
    global votes, game_interrupt, current_player, scores, voice_channel
    players = [m for m in voice_channel.members if not m.bot]
    while not players:
        await asyncio.sleep(1)
        players = [m for m in ctx.channel.members if not m.bot and m.voice and m.voice.channel.name == voice_channel]
    random.shuffle(players)

    # print the turn order
    await ctx.send('Turn order is: ' + ', '.join(player.name for player in players))

    while cards:
        for player in players:
            current_player = player
            if cards:
                card = cards.pop()
                votes = {}  # Clear previous votes
                game_interrupt.clear()  # Clear previous interrupt event
                no_points_card = card.startswith('*')
                if no_points_card:
                    card = card[1:]  # remove the '*' from the front for displaying
                await ctx.send(f'{player.mention}, your card is: {card}. Others, please vote using `!vote pass` or `!vote fail`.' +
                               ('\nNO POINTS' if no_points_card else ''))
                
                await game_interrupt.wait()  # Wait until a majority of votes are in
                
                pass_votes = len([v for v in votes.values() if v == 'pass'])
                fail_votes = len([v for v in votes.values() if v == 'fail'])

                if pass_votes > fail_votes:
                    if not no_points_card:
                        await ctx.send(f'Majority voted pass! Well done, {player.mention}!')
                        scores[player] = scores.get(player, 0) + 1  # add a point to the player's score
                    else:
                        await ctx.send(f'Majority voted pass! This was a no-score card, {player.mention}!')
                else:
                    await ctx.send(f'Majority voted fail. Better luck next time, {player.mention}!')
                    cards.append('*' + card if no_points_card else card)  # return the card to the pack
                    random.shuffle(cards)  # shuffle the pack
            else:
                break
    await ctx.send('Game finished.')

@bot.command(name='shuffle', aliases=['sh'])
async def shuffle(ctx):
    global cards
    random.shuffle(cards)
    await ctx.send('Cards shuffled.')

@bot.command(name='end-game', aliases=['eg'])
async def end_game(ctx):
    global scores, cards, expansions, votes, game_interrupt, voice_channel
    score_report = "Game ended. Here's the final scores:\n"
    for player, score in scores.items():
        score_report += f'{player.name}: {score}\n'
    await ctx.send(score_report)
    # Reset game data
    scores = {}
    cards = []
    expansions = {}
    votes = {}
    game_interrupt.clear()
    voice_channel = None

# Add your token here
bot.run('your-key-here')
