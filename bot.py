import discord
from discord import app_commands
from discord.ext import commands
import json
import random
import time
import os

DB_FILE = "users.json"

def load_users():
    if not os.path.isfile(DB_FILE):
        with open(DB_FILE, "w") as f:
            json.dump({}, f)
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(DB_FILE, "w") as f:
        json.dump(users, f, indent=2)

def get_user(users, user_id):
    if str(user_id) not in users:
        users[str(user_id)] = {"balance": 100, "last_daily": 0}
    return users[str(user_id)]

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}!")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print(f"Sync failed: {e}")

@bot.tree.command(name="balance", description="Check your coin balance")
async def balance(interaction: discord.Interaction):
    users = load_users()
    user = get_user(users, interaction.user.id)
    await interaction.response.send_message(f"💰 You have {user['balance']} coins.")

@bot.tree.command(name="daily", description="Claim your daily 50 coins")
async def daily(interaction: discord.Interaction):
    users = load_users()
    user = get_user(users, interaction.user.id)
    now = int(time.time())
    if now - user["last_daily"] < 86400:
        await interaction.response.send_message("⏳ You already claimed your daily coins. Come back later.")
        return
    user["balance"] += 50
    user["last_daily"] = now
    save_users(users)
    await interaction.response.send_message(f"🎁 You claimed 50 daily coins! Balance: {user['balance']}")

@bot.tree.command(name="give", description="Give coins to another user")
@app_commands.describe(user="User to give coins to", amount="Amount of coins to give")
async def give(interaction: discord.Interaction, user: discord.User, amount: int):
    if amount <= 0:
        await interaction.response.send_message("❌ Amount must be positive.")
        return
    if user.id == interaction.user.id:
        await interaction.response.send_message("❌ You cannot give coins to yourself.")
        return
    users = load_users()
    giver = get_user(users, interaction.user.id)
    receiver = get_user(users, user.id)
    if giver["balance"] < amount:
        await interaction.response.send_message("❌ You do not have enough coins.")
        return
    giver["balance"] -= amount
    receiver["balance"] += amount
    save_users(users)
    await interaction.response.send_message(f"✅ You gave {amount} coins to {user.mention}. Your balance: {giver['balance']}")

@bot.tree.command(name="coinflip", description="Bet on a coinflip")
@app_commands.describe(choice="Heads or Tails", amount="Amount to bet")
@app_commands.choices(choice=[
    app_commands.Choice(name="heads", value="heads"),
    app_commands.Choice(name="tails", value="tails"),
])
async def coinflip(interaction: discord.Interaction, choice: app_commands.Choice[str], amount: int):
    if amount <= 0:
        await interaction.response.send_message("❌ Bet amount must be positive.")
        return
    users = load_users()
    user = get_user(users, interaction.user.id)
    if user["balance"] < amount:
        await interaction.response.send_message("❌ Not enough coins.")
        return
    result = random.choice(["heads", "tails"])
    win = (choice.value == result)
    if win:
        user["balance"] += amount
        save_users(users)
        await interaction.response.send_message(f"🎉 Coinflip result: **{result}**! You won {amount} coins! Balance: {user['balance']}")
    else:
        user["balance"] -= amount
        save_users(users)
        await interaction.response.send_message(f"😢 Coinflip result: **{result}**! You lost {amount} coins. Balance: {user['balance']}")

@bot.tree.command(name="roulette", description="Bet on roulette (red, black, green)")
@app_commands.describe(color="Color to bet on", amount="Amount to bet")
@app_commands.choices(color=[
    app_commands.Choice(name="red", value="red"),
    app_commands.Choice(name="black", value="black"),
    app_commands.Choice(name="green", value="green"),
])
async def roulette(interaction: discord.Interaction, color: app_commands.Choice[str], amount: int):
    if amount <= 0:
        await interaction.response.send_message("❌ Bet amount must be positive.")
        return
    users = load_users()
    user = get_user(users, interaction.user.id)
    if user["balance"] < amount:
        await interaction.response.send_message("❌ Not enough coins.")
        return

    # Roulette wheel simulated with numbers 0-36
    # 0 = green, ~18 red, ~18 black randomly assigned
    wheel = []
    # Green 0
    wheel.append("green")
    # Assign red and black 18 each randomly
    wheel.extend(["red"] * 18)
    wheel.extend(["black"] * 18)
    spin = random.choice(wheel)

    if spin == color.value:
        if color.value == "green":
            winnings = amount * 14
        else:
            winnings = amount * 2
        user["balance"] += winnings
        save_users(users)
        await interaction.response.send_message(f"🎉 The wheel landed on **{spin}**! You won {winnings} coins! Balance: {user['balance']}")
    else:
        user["balance"] -= amount
        save_users(users)
        await interaction.response.send_message(f"😢 The wheel landed on **{spin}**. You lost {amount} coins. Balance: {user['balance']}")

# Simple blackjack implementation (player vs bot, no splits, no double downs, bot hits <17)
@bot.tree.command(name="blackjack", description="Play blackjack against the bot")
@app_commands.describe(amount="Bet amount")
async def blackjack(interaction: discord.Interaction, amount: int):
    if amount <= 0:
        await interaction.response.send_message("❌ Bet amount must be positive.")
        return
    users = load_users()
    user = get_user(users, interaction.user.id)
    if user["balance"] < amount:
        await interaction.response.send_message("❌ Not enough coins.")
        return

    # Deck simplified (only values matter here)
    cards = [2,3,4,5,6,7,8,9,10,10,10,10,11] * 4
    random.shuffle(cards)

    def score(hand):
        s = sum(hand)
        # adjust aces from 11 to 1 if bust
        aces = hand.count(11)
        while s > 21 and aces:
            s -= 10
            aces -=1
        return s

    player_hand = [cards.pop(), cards.pop()]
    dealer_hand = [cards.pop(), cards.pop()]

    # Player hits until 17 or more (auto simple AI for now)
    while score(player_hand) < 17:
        player_hand.append(cards.pop())
    player_score = score(player_hand)
    dealer_score = score(dealer_hand)

    # Dealer hits under 17
    while dealer_score < 17:
        dealer_hand.append(cards.pop())
        dealer_score = score(dealer_hand)

    # Outcome
    if player_score > 21:
        # bust
        user["balance"] -= amount
        save_users(users)
        await interaction.response.send_message(f"😵 You busted with {player_score}! You lost {amount} coins. Balance: {user['balance']}")
    elif dealer_score > 21 or player_score > dealer_score:
        user["balance"] += amount
        save_users(users)
        await interaction.response.send_message(f"🎉 You won! Your hand: {player_hand} ({player_score}), Dealer's hand: {dealer_hand} ({dealer_score}). You won {amount} coins! Balance: {user['balance']}")
    elif player_score == dealer_score:
        await interaction.response.send_message(f"🤝 It's a tie! Your hand: {player_hand} ({player_score}), Dealer's hand: {dealer_hand} ({dealer_score}). Your balance stays at {user['balance']}")
    else:
        user["balance"] -= amount
        save_users(users)
        await interaction.response.send_message(f"😞 You lost! Your hand: {player_hand} ({player_score}), Dealer's hand: {dealer_hand} ({dealer_score}). You lost {amount} coins. Balance: {user['balance']}")

# Tic-tac-toe simplified: just start a challenge, no full game flow (too complex for one message)
@bot.tree.command(name="tictactoe", description="Challenge someone to tic-tac-toe")
@app_commands.describe(opponent="Opponent user to play with")
async def tictactoe(interaction: discord.Interaction, opponent: discord.User):
    if opponent.bot:
        await interaction.response.send_message("❌ You cannot challenge a bot.")
        return
    if opponent.id == interaction.user.id:
        await interaction.response.send_message("❌ You cannot challenge yourself.")
        return
    await interaction.response.send_message(f"🎮 {interaction.user.mention} has challenged {opponent.mention} to tic-tac-toe! (Game implementation TBD)")

bot.run("YOUR_BOT_TOKEN")
