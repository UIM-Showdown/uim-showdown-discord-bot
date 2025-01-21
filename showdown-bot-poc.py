import argparse
import configparser
import logging
import showdownbot.showdownbot as showdownbot

# Set up logging
logging.basicConfig(filename='showdown.log', encoding='utf-8', level=logging.INFO)

# Parse command-line args
parser = argparse.ArgumentParser(
  prog = 'Showdown Bot POC',
  description = 'POC for the UIM Showdown bot'
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