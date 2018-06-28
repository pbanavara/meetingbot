### A Slack conversational bot for scheduling and monitoring meetings

#### Just an attempt to write a conversational interface for scheduling and monitoring time spent in meetings.

[Demo](https://www.youtube.com/watch?v=XWFw_gN5EaM)

* I intend to focus on analyzing the time spent and other issues related to meetings, scheduling is just a hook. It's incredibly hard to do dialog based scheduling.
* I have used SuTime from StanfordCoreNLP and the respective Python wrapper
##### Steps to run locally

###### Pre-requisites
* Setup a slack bot user. [Instructions](https://api.slack.com/bot-users)
* Retrieve and store the slack auth name and the auth token
* [Setup](https://developers.google.com/calendar/quickstart/python) a Google calendar API (Optional if you just want to use my API)
    * While setting this up choose the webserver option and Other webservers.
* Store the Google Calendar API secret in client_secret.json.
* Install [python-sutime](https://github.com/FraBle/python-sutime)
* Export the following environment variables. You can store these in a source file or in your shell start script.
    ```
    export SLACK_AUTH_NAME=<Bot Username>
    export SLACK_AUTH_TOKEN=<Auth Token>
    export LC_ALL=en_US.UTF-8
    export LANG=en_US.UTF-8
    ```
* Run `pip install -r requirements.txt`
* Run `python starter.py`
* You are now ready to start issuing slack commands as the bot user comes online
* Sample commands : 
    * "Schedule a meeting today evening at 8 PM for 1 hour"
    * "Schedule a meetting with <slackuser> today from Noon to 1PM"
    * "Get me a summary"



