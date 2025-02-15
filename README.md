# UIM Showdown - Python Discord Bot

A Discord bot created for the UIM Showdown competition, implemented in Python and built around the discord.py package

## Setup

* Install the bot
  * Clone this repo: `git clone https://github.com/kuhnertdm/uim-showdown-python-bot-poc.git`
  * Install the latest version of [Python 3](https://www.python.org/downloads/)
    * Python 3.5 or later is required due to the usage of the typing module
  * Install the "discord.py" package via pip:
    * Windows: `py -3 -m pip install -U discord.py`
    * Linux: `python3 -m pip install -U discord.py`
  * Install the Google APIs via pip:
    * Windows: `py -3 -m pip install -U google-api-python-client google-auth-httplib2 google-auth-oauthlib`
    * Linux: `python3 -m pip install -U google-api-python-client google-auth-httplib2 google-auth-oauthlib`
* Set up the required Google sheets
  * The bingo info sheet should have the following tabs:
    * Form Responses 1 - The output of the signup form. The bot reads the Discord tag from the fourth column, as it is the fourth question in the signup form.
    * Team Rosters - Contains three columns: "Discord Name", "RSN", and "Team", for the Discord tag, RSN, and full team name respectively
      * This will be empty until the draft, except for the headers
    * Team Info - Contains three columns: "Team Name", "Tag", and "Color", for the full team name, abbreviation (used for channel names), and team color (used for roles, format "#A1B2C3") respectively
      * This will be empty until the draft, except for the headers
    * Monsters - Contains one column with no header, each row is a different monster name
    * Collection Log Items - Contains one column with no header, each row is a different item name
    * Challenges - Contains one column with no header, each row is a different challenge name
  * The submission sheet should have a tab for each type of submission; the rest depends on the type of submission and how the ingest bot is interpreting the data.
  * The Google service account's email address (ending in ".iam.gserviceaccount.com") should have editor access to the submission sheet, and at least viewer access to the bingo info sheet. I recommend giving it editor access to the bingo info sheet in case you ever want to automate the process of populating bingo info in the future.
* Download the credential file for the Google Cloud service account and save it to the directory as "google-creds.json"
* Create a config.ini file at the root of the project directory (format documented below)
* At this point, you can begin calling the --updatecompetitorrole command on a scheduled job to automatically add the "Competitor" role to all signed up Discord members:
  * Windows: `py -3 ./showdownrunner.py --updatecompetitorrole`
  * Linux: `python3 ./showdownrunner.py --updatecompetitorrole`
* Once the draft is complete, populate the "Team Rosters" and "Team Info" tabs on the bingo info sheet
* Set up the team roles/categories/channels:
  * Windows: `py -3 ./showdownrunner.py --setupserver`
  * Linux: `python3 ./showdownrunner.py --setupserver`
* Update the command list in the server:
  * Windows: `py -3 ./showdownrunner.py --updatecommands`
  * Linux: `python3 ./showdownrunner.py --updatecommands`
* Run the bot:
  * Windows: `py -3 ./showdownrunner.py`
  * Linux: `python3 ./showdownrunner.py`
  * This command will continue running until the process is killed
* After the event is over, you can also automatically delete the team roles/categories/channels:
  * Windows: `py -3 ./showdownrunner.py --teardownserver`
  * Linux: `python3 ./showdownrunner.py --teardownserver`

## Discord Permissions

The following are the required privileged gateway intents for the bot:

* Server Members Intent
* Message Content Intent

The following are the required OAuth2 scopes for the bot:

* bot
* applications.commands

The following are the required permissions for the bot:

* Manage Roles
* Manage Channels
* View Channels
* Send Messages
* Manage Messages

## Components

The following are the major components of this repo:

* **showdownrunner.py:** Runner script for the bot, reads config file and command-line input, constructs a ShowdownBot object, and calls run() on it.
* **showdownbot/showdownbot.py:** Defines the ShowdownBot class, which is a wrapper for the discord.py library's "Bot" class, contains most event logic, and defines command handler methods that act as the entry points for actions triggered by slash commands.
* **submissions.py:** Defines the Submission class, which contains information for a submission made via the bot. Also contains serializer/deserializer methods for the class so that a submission can be included within the text of a Discord message (this is used to store state between when a submission is made and when it is approved).
* **approvalhandlers.py:** Defines a number of classes that inherit from the ApprovalHandler ABC. These classes define a "submissionApproved" method that acts as a callback for when a submission is approved, and generally involve writing new rows to the submission sheet.
* **googlesheetclient.py:** Defines the GoogleSheetClient class for interfacing with the bingo info/submission sheets.
* **errors.py:** Defines the BingoUserError class, which inherits from Exception and represents an exception that is caused by user error (e.g. invalid input)

## The ShowdownBot Class

The following are the major components of the ShowdownBot class:

* **__init__():** The constructor for the class. Does the following:
  * Sets up instance variables based on the config properties passed in
  * Creates the Bot object (from the discord.py library) used as a client to communicate with Discord
  * Calls helper methods (detailed below) to do the following:
    * Register command callbacks
    * Register the error handler callback
    * Register the interaction hook
    * Register the ready hook
* **registerCommands():** Defines command callbacks and registers them with the bot. Each callback method is decorated with an @self.bot.tree.command decorator, which automatically adds the command to the bot's command tree.
* **registerErrorHandler():** Defines and registers the error handler callback, which replies to the interaction with the exception message if it is a BingoUserError, and otherwise reports an internal error to the error channel.
* **registerInteractionHook():** Defines and registers the interaction hook for the bot, which is called upon all user interactions in the server. If the interaction is a button click on a button with ID "approve" or "deny", handles the action for approving or denying a submission.
* **registerReadyHook():** Defines and registers the ready hook, which is called upon first connecting to Discord. Calls methods to populate instance variables with data from the bingo info sheet and the Discord server, and to handle command-line flags that cause the bot to do something other than starting up normally (e.g. setting up or tearing down the server).
* **start():** Calls run() on the underlying Bot object (from the discord.py library)

## Adding a command

To add a new command to the bot, do the following:

* Add a function to the ShowdownBot's registerCommands() method annotated with @self.bot.tree.command to define the command and input validation logic. It must call self.createSubmission(), and then send a message back to confirm the action.
* Create an approval handler class in approvalhandlers.py. This class's submissionApproved() method must handle any non-Discord-facing actions that must be taken when the submission is approved.
* Assign the approval handler to the command at the top of submissions.py.
* To register the command in the Discord server, run the bot with the --updatecommands flag: `py -3 ./showdownrunner.py --updatecommands`
  * Try to avoid spamming command updates; Discord will rate-limit the bot if it receives too many update requests.
  * This is not necessary for changes to the code within a command; it is only needed when adding a new command, or changing the syntax of a command (i.e. what parameters it takes)

## Changing team rosters (e.g. after a trade or replacement)

The bot does *not* handle this automatically, you will need to do most of it manually:

* Modify the Discord roles for the relevant players as needed
* Modify the "Team Rosters" tab of the bingo info sheet as needed
* If the bot is currently running, restart it so it can pull the new version of the bingo info sheet at startup

## config.ini format

**DO NOT INCLUDE THE CONFIG.INI FILE IN VERSION CONTROL; IT CONTAINS SECRETS. IT IS INCLUDED IN THE .GITIGNORE FILE SO IT WILL NOT BE AUTOMATICALLY INCLUDED.**

```
[BingoProperties]
token = <API token goes here>
submissionQueueChannelId = <Channel ID for the submission queue channel goes here>
submissionLogChannelId = <Channel ID for the submission log channel goes here>
errorsChannelId = <Channel ID for the errors channel goes here>
guildId = <Discord server ID goes here>
submissionSheetId = <Google Sheets spreadsheet ID for player submissions goes here>
bingoInfoSheetId = <Google Sheets spreadsheet ID for signup/team/other info goes here>
```