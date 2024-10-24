import argparse
import configparser
import showdownbot.showdownbot as showdownbot

# Parse command-line args
parser = argparse.ArgumentParser(
  prog = 'Showdown Bot POC',
  description = 'POC for the UIM Showdown bot'
)
parser.add_argument('--updatecommands', action='store_true')
commandLineArgs = parser.parse_args()

# Load config file
config = configparser.ConfigParser()
config.read('config.ini')

showdownBot = showdownbot.ShowdownBot(commandLineArgs, config)
showdownBot.start()