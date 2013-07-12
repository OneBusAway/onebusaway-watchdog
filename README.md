onebusaway-watchdog
===================

onebusaway-watchdog is a Python-based watchdog application for your [OneBusAway (OBA)](http://onebusaway.org/) REST API server that 
occasionally checks API responses for valid real-time transit data.  It keeps an eye on your OBA server
so you don't have to.

onebusaway-watchdog performs the following tasks:

1.  Tests for the success of various API queries on OBA.
2.  Tests that there is realtime data available for >50% of buses currently running.
3.  Tests that unrealistic results (e.g.,100% ontime performance) aren't being returned

If an issue is detected, an email is generated with an Alert # and a description of the problem.
The watchdog will then stop running until that Alert is addressed (to prevent emails would keep piling up).
When someone replies back to the email, the Alert is closed and the watchdog resumes.

### Setup
Since onebusaway-watchdog generates email alerts, it requires the email addresses of the people
to contact when there are problems, as well as the credentials for an email server.  Currently,
this information is hard-coded in the script, so you'll need to edit this to meet your needs.

Similarly, the script requires a OneBusAway REST API server address.  This also currently needs
to be edited manually.

You'll also need a [Python interpreter](http://www.python.org/getit/) to run the script.

### Usage

At the command-line, execute:

`check_oba.py`
