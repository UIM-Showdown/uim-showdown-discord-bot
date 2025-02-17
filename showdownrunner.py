import argparse
import configparser
import logging
import showdownbot.showdownbot as showdownbot

# Set up logging
logging.basicConfig(filename='showdown.log', encoding='utf-8', level=logging.ERROR, format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logging.getLogger('discord.client').setLevel(logging.WARN)
logging.getLogger('discord.gateway').setLevel(logging.WARN)
logging.getLogger('discord.http').setLevel(logging.WARN)
log = logging.getLogger('showdown')
log.addHandler(logging.StreamHandler())
log.setLevel(logging.INFO)
log.info('Starting Showdown Bot')

# Parse command-line args
parser = argparse.ArgumentParser(
  prog = 'UIM Showdown - Discord Bot',
  description = 'A Discord bot created for the UIM Showdown competition, implemented in Python and built around the discord.py package'
)
parser.add_argument('--clearcommands', action='store_true', help='Clears command list on the Discord server - DO NOT SPAM THIS OR YOU WILL BE RATE LIMITED')
parser.add_argument('--updatecommands', action='store_true', help='Updates command list on the Discord server - DO NOT SPAM THIS OR YOU WILL BE RATE LIMITED')
parser.add_argument('--updatecompetitorrole', action="store_true", help='Assigns "Competitor" role and exits')
parser.add_argument('--setupserver', action='store_true', help='Creates team roles/categories/channels and assigns roles to players, and exits')
parser.add_argument('--teardownserver', action='store_true', help='Deletes team roles/categories/channels, and exits')
commandLineArgs = parser.parse_args()

# Load config file
config = configparser.ConfigParser()
config.read('config.ini')

showdownBot = showdownbot.ShowdownBot(commandLineArgs, config)
showdownBot.start()