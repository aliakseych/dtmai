import argparse
import asyncio
from src.controllers.website import main as website_main
from src.controllers.bot import main as bot_main

from src.settings import settings

parser = argparse.ArgumentParser(description="DTM AI services launcher")
parser.add_argument(
    "service",
    help="Service: either bot or website",
)
args = parser.parse_args()

if args.service == "bot":
    asyncio.run(bot_main.main(settings))
elif args.service == "website":
    asyncio.run(website_main.main(settings))
