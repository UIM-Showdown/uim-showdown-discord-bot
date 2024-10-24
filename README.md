# UIM Showdown - Python Discord Bot POC

A POC for a Python version of the UIM Showdown Discord bot

## Setup

* Install the latest version of [Python 3](https://www.python.org/downloads/)
  * Python 3.5 or later is required due to the usage of the typing module
* Install the "discord.py" package via pip:
  * Windows: `py -3 -m pip install -U discord.py`
  * Linux: `python3 -m pip install -U discord.py`
* Bug workaround in discord.py as of 10/23: Install the "audioop-lts" package via pip:
  * Windows: `py -3 -m pip install -U audioop-lts`
  * Linux: `python3 -m pip install -U audioop-lts`
* Create a config.ini file at the root of the project directory (format documented below)
* Verify that the contents of the bingo-info directory are up to date
* Update the command list in the server:
  * Windows: `py -3 ./showdown-bot-poc.py --updatecommands`
  * Linux: `python3 ./showdown-bot-poc.py --updatecommands`
* Run the bot:
  * Windows: `py -3 ./showdown-bot-poc.py`
  * Linux: `python3 ./showdown-bot-poc.py`

## Code flows

### Starting the bot:

* Admin runs showdown-bot-poc.py
* showdown-bot-poc.py parses command-line args and loads the config.ini file
* showdown-bot-poc.py creates a ShowdownBot object
* The ShowdownBot constructor handles all initialization for the bot, including loading commands and initializing config info from the provided command-line args and config properties
* showdown-bot-poc.py calls start() on the ShowdownBot object to connect it to Discord

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
* Back in the button's callback method, it removes the buttons, sends a sucess message to the approvals channel, and then sends the "approved" message back to the submissions channel

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

**DO NOT INCLUDE THE CONFIG.INI FILE IN VERSION CONTROL; IT CONTAINS SECRETS.**

```
[BingoProperties]
token = <API token goes here>
approvalsChannelId = <Channel ID for the approvals channel goes here>
errorsChannelId = <Channel ID for the errors channel goes here>
guildId = <Discord server ID goes here>
```