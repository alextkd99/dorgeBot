import discord
import asyncio
import requests
from google.cloud import firestore

# Initialize Firestore client
db = firestore.Client()

# Discord Bot setup
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# Your Discord Bot Token, Riot API Key, Summoner Name, and Region
DISCORD_TOKEN = 'token'
CHANNEL_ID = 000
RIOT_API_KEY = 'apikey'
SUMMONER_NAME = 'summoner_name'
REGION = 'Region'

async def fetch_tft_rank(summoner_name):
    """Fetches the current TFT rank of the specified summoner."""
    url_summoner = f"https://{REGION}.api.riotgames.com/tft/summoner/v1/summoners/by-name/{summoner_name}"
    headers = {"X-Riot-Token": RIOT_API_KEY}
    response_summoner = requests.get(url_summoner, headers=headers)
    if response_summoner.status_code == 200:
        summoner_id = response_summoner.json()['id']
        url_rank = f"https://{REGION}.api.riotgames.com/tft/league/v1/entries/by-summoner/{summoner_id}"
        response_rank = requests.get(url_rank, headers=headers)
        if response_rank.status_code == 200:
            rank_data = response_rank.json()
            if rank_data:
                # Assuming the player has a rank and taking the first entry
                current_rank = f"{rank_data[0]['tier']} {rank_data[0]['rank']}"
                return current_rank
    return "Rank not found"

async def check_and_update_rank():
    """Checks the current rank, updates Firestore, and sends a Discord message if there's a change."""
    channel = client.get_channel(CHANNEL_ID)
    if channel is None:
        print("Channel not found.")
        return

    current_rank = await fetch_tft_rank(SUMMONER_NAME)
    doc_ref = db.collection('tft_ranks').document(SUMMONER_NAME)
    doc = doc_ref.get()
    if doc.exists:
        previous_rank = doc.to_dict().get('current_rank')
        if current_rank != previous_rank:
            await channel.send(f"Rank update for {SUMMONER_NAME}: {previous_rank} -> {current_rank}")
            doc_ref.update({"current_rank": current_rank, "previous_rank": previous_rank})
    else:
        await channel.send(f"Rank recorded for {SUMMONER_NAME}: {current_rank}")
        doc_ref.set({"current_rank": current_rank, "previous_rank": current_rank})


@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    client.loop.create_task(schedule_rank_checks())

async def schedule_rank_checks():
    await client.wait_until_ready()
    while not client.is_closed():
        await check_and_update_rank()
        await asyncio.sleep(600)  # Wait for 600 seconds (10 minutes) before next check

client.run(DISCORD_TOKEN)
