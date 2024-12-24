# UIM Showdown - Python Discord Bot POC

A POC for a Python version of the UIM Showdown Discord bot

## Setup

* Install the bot
  * Clone this repo: `git clone https://github.com/kuhnertdm/uim-showdown-python-bot-poc.git`
  * Install the latest version of [Python 3](https://www.python.org/downloads/)
    * Python 3.5 or later is required due to the usage of the typing module
  * Install the "discord.py" package via pip:
    * Windows: `py -3 -m pip install -U discord.py`
    * Linux: `python3 -m pip install -U discord.py`
  * Bug workaround in discord.py as of 10/23: Install the "audioop-lts" package via pip:
    * Windows: `py -3 -m pip install -U audioop-lts`
    * Linux: `python3 -m pip install -U audioop-lts`
  * Install the Google APIs via pip:
    * Windows: `py -3 -m pip install -U google-api-python-client google-auth-httplib2 google-auth-oauthlib`
    * Linux: `python3 -m pip install -U google-api-python-client google-auth-httplib2 google-auth-oauthlib`
* Set up the required Google sheets
  * The bingo info sheet should have the following tabs:
    * Signups - The output of the signup form. The Discord tag for the user needs to be the first column.
    * Team Rosters - Contains three columns: "Discord Name", "RSN", and "Team", for the Discord tag, RSN, and full team name respectively
      * This will be empty until the draft, except for the headers
    * Team Info - Contains three columns: "Team Name", "Tag", and "Color", for the full team name, abbreviation (used for channel names), and team color (used for roles, format "#A1B2C3") respectively
      * This will be empty until the draft, except for the headers
    * Monsters - Contains one column with no header, each row is a different monster name
    * Collection Log Items - Contains one column with no header, each row is a different item name
  * The submission sheet should have a tab for each type of submission; the rest depends on the type of submission and how the ingest bot is interpreting the data.
  * The Google service account's email address (ending in ".iam.gserviceaccount.com") should have editor access to the submission sheet, and at least viewer access to the bingo info sheet. I recommend giving it editor access to the bingo info sheet in case you ever want to automate the process of populating bingo info in the future.
* Download the credential file for the Google Cloud service account and save it to the directory as "google-creds.json"
* Create a config.ini file at the root of the project directory (format documented below)
* At this point, you can begin calling the --updatesignuproles command on a scheduled job to automatically add the "Signup" role to all signed up Discord members, and the "Competitor" role to all Discord members on a team:
  * Windows: `py -3 ./showdown-bot-poc.py --updatesignuproles`
  * Linux: `python3 ./showdown-bot-poc.py --updatesignuproles`
* Once the draft is complete, populate the "Team Rosters" and "Team Info" tabs on the bingo info sheet
* Set up the team roles/categories/channels:
  * Windows: `py -3 ./showdown-bot-poc.py --setupserver`
  * Linux: `python3 ./showdown-bot-poc.py --setupserver`
* Update the command list in the server:
  * Windows: `py -3 ./showdown-bot-poc.py --updatecommands`
  * Linux: `python3 ./showdown-bot-poc.py --updatecommands`
* Run the bot:
  * Windows: `py -3 ./showdown-bot-poc.py`
  * Linux: `python3 ./showdown-bot-poc.py`
  * This command will continue running until the process is killed
* After the event is over, you can also automatically delete the team roles/categories/channels:
  * Windows: `py -3 ./showdown-bot-poc.py --teardownserver`
  * Linux: `python3 ./showdown-bot-poc.py --teardownserver`

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

## Code flows

### Starting the bot:

* Admin runs showdown-bot-poc.py
* showdown-bot-poc.py parses command-line args and loads the config.ini file
* showdown-bot-poc.py creates a ShowdownBot object
* The ShowdownBot constructor handles all initialization for the bot, including loading commands and initializing config info from the provided command-line args and config properties
* showdown-bot-poc.py calls start() on the ShowdownBot object to connect it to Discord
* Discord.py library calls the on_ready() method, which checks for alternate run commands (e.g. --setupserver etc)
* If an alternate run command is present, the on_ready() method calls the appropriate method for that command, and then exits
* Otherwise (meaning the bot is being ran normally), the on_ready() method loads the bingo info from the bingo info sheet and prints a message to indicate that it is connected

### Submitting a request:

* User calls an application command (slash command)
* Discord.py library runs the code in the method annotated with @self.bot.tree.command in showdownbot.py
* Command method handles input validation (e.g. KCs must not be negative, pick-list values must be in the pick-list, etc), and if this validation fails, it raises a BingoUserError
* Command method creates an ApprovalRequest object from the context (which is an Interaction object) and passes it to requestApproval(), then sends back a confirmation message
* requestApproval() sends a message to the approvals channel with the request details, and constructs custom button subclasses to include with it, which include callback methods and the request info

### Approving a request:

* Staff member clicks the approve button on the message in the approvals channel
* The callback method in the ApproveButton class is called
* The callback method calls the approve() method on the ApprovalRequest object (which was stored on the button)
* ApprovalRequest.approve() calls requestApproved() on its approval handler
* The approval handler's requestApproved() method handles things like talking to the spreadsheet
* Back in the button's callback method, it removes the buttons, sends a sucess message to the approvals channel, and then sends the "approved" message back to the player's submission channel

### Denying a request:

* Staff member clicks the deny button on the message in the approvals channel
* The callback method in the DenyButton class is called
* The callback method remove the buttons, sends a sucess message to the approvals channel, and then sends the "denied" message back to the submissions channel

### User error handling:

* Command method raises a BingoUserError due to failed input validation
* Discord.py library runs the code in the method annotated with @self.bot.tree.error in showdownbot.py
* Command error handler callback method calls handleCommandError()
* handleCommandError() sees that the error is a BingoUserError and simply sends a message back with the error text

### Unexpected error handling:

* Command method raises an error other than BingoUserError due to an unexpected error
* Discord.py library runs the code in the method annotated with @bot.tree.error in showdownbot.py
* Command error handler callback method calls handleCommandError()
* handleCommandError() sees that the error is not a BingoUserError and sends a message to the errors channel listing the request/error details

## Adding a command

* Add a function to the ShowdownBot constructor annotated with @self.bot.tree.command to define the command and input validation logic. It must call self.requestApproval(), and then send a message back with request info.
* Create an approval handler class in approvalhandlers.py. This class's requestApproved() method handles any non-Discord-facing actions that must be taken when the request is approved.
* Assign the approval handler to the command at the top of approvalrequest.py.
* Everything outside of input validation and approval handling is already handled by the bot's core code.
* To register the command in the Discord server, run the bot with the --updatecommands flag: `py -3 ./showdown-bot-poc.py --updatecommands`
  * Try to avoid spamming command updates; Discord will rate-limit the bot if it receives too many update requests.
  * This is not necessary for changes to the code within a command; it is only needed when adding a new command, or changing the syntax of a command (i.e. what parameters it takes)

## config.ini format

**DO NOT INCLUDE THE CONFIG.INI FILE IN VERSION CONTROL; IT CONTAINS SECRETS. IT IS INCLUDED IN THE .GITIGNORE FILE SO IT WILL NOT BE AUTOMATICALLY INCLUDED.**

```
[BingoProperties]
token = <API token goes here>
approvalsChannelId = <Channel ID for the approvals channel goes here>
errorsChannelId = <Channel ID for the errors channel goes here>
guildId = <Discord server ID goes here>
submissionSheetId = <Google Sheets spreadsheet ID for player submissions goes here>
bingoInfoSheetId = <Google Sheets spreadsheet ID for player signups and team rosters goes here>
```