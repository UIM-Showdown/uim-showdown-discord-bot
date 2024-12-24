import argparse
import configparser
import showdownbot.showdownbot as showdownbot

# Parse command-line args
parser = argparse.ArgumentParser(
  prog = 'Showdown Bot POC',
  description = 'POC for the UIM Showdown bot'
)
# TODO add descriptions for these
parser.add_argument('--updatecommands', action='store_true', help='Updates command list on the Discord server - DO NOT SPAM THIS OR YOU WILL BE RATE LIMITED')
parser.add_argument('--updatesignuproles', action="store_true", help='Assigns "Signup" and "Competitor" roles and exits')
parser.add_argument('--setupserver', action='store_true', help='Creates team roles/categories/channels and assigns roles to players, and exits')
parser.add_argument('--teardownserver', action='store_true', help='Deletes team roles/categories/channels, and exits')
commandLineArgs = parser.parse_args()

# Load config file
config = configparser.ConfigParser()
config.read('config.ini')

showdownBot = showdownbot.ShowdownBot(commandLineArgs, config)
showdownBot.start()