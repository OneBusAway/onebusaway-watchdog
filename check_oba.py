#!/usr/bin/env python

"""
Copyright 2013 Georgia Institute of Technology

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import urllib2
import urllib
import json
import datetime
import csv
import time

import textmarks_v2api_client

import os
import smtplib

from email import Encoders
from email.MIMEBase import MIMEBase
from email.MIMEMultipart import MIMEMultipart
from email.Utils import formatdate
from email.mime.text import MIMEText

#####PARAMETERS#######
realtime_agencies = ['MARTA'] #Agency ids for agencies with realtime data.
alert_list = ["user1@gmail.com" , "user2@gatech.edu" , "user3@gmail.com"] #These people get an email every time there is an alert.
report_list = ["user1@gmail.com" , "user2@gatech.edu" , "user3@gmail.com"] #These people get an email every time that check_oba.py is run
from_address = 'onebusawayatl@gatech.edu'

csv_status_file = '/home/derek/OBA_Alerts/alert_status.csv'
root_url = 'http://onebusaway.gatech.edu/api'

report_frequency = 15 #This is how often a report is generated.  Measured in minutes.

START_OF_DAY = 6 #The hour that we start checking, we stop at midnight
HOST = 'imap.gmail.com'
USERNAME = 'onebusawayatl'
PASSWORD = 'emailpassword'
#######################

def getAgencies(apiURL, attempts=0):
        base = apiURL + '/api/where/agencies-with-coverage.json?'
        query = urllib.urlencode({'key' : 'TEST'})

        try:
                response = urllib2.urlopen(base + query, timeout=30).read()
        except IOError as e:
		if attempts > 3:
			return False, 'Unable to open:  ' + base + query
		else:
			time.sleep(20)
			print 'getAgencies sleeping'
			return(getAgencies(apiURL, attempts+1))

        except urllib2.URLError, e:
                return False, "Timeout when opening:  " + base + query
        try:
                data = json.loads(response)
        except ValueError:
                return False, 'NO JSON Data in getAgencies: ' + base + query
        except error:
                return False, 'UNKNOWN ERROR in getAgencies' + base + query

        try:
                agencies = data['data']['list']
        except KeyError:
                return False, 'Agency list not formatted as expected: ' + base + query
        return True, agencies


def getStops(apiURL, agency, attempts=0):
        base = apiURL + '/api/where/stop-ids-for-agency/' + agency['agencyId'] + '.json?'
        query = urllib.urlencode({'key' : 'TEST'})

        try:
                response = urllib.urlopen(base + query).read()
        except IOError as e:
		if attempts > 3:
			return False, 'Unable to open:  ' + base + query
		else:
			time.sleep(20)
			print 'getStops sleeping'
			return(getStops(apiURL, agency, attempts+1))

        except urllib2.URLError, e:
                return False, "Timeout when opening:  " + base + query

        try:
                data = json.loads(response)
        except ValueError:
                return False, 'NO JSON Data in getStops: ' + base + query
        except error:
                return False, 'UNKNOWN ERROR in getStops' + base + query


        try:
                stops = data['data']['list']
        except KeyError:
                return False, 'Stops list not formatted as expected: ' + base + query

        return True, stops

def checkArrivals(apiURL, stop, arr, attempts=0):
        base = apiURL + '/api/where/arrivals-and-departures-for-stop/' + stop + '.json?'

        # Checks arrivals and departures for a stop that occur only in the next 10 minutes because we don't really care about buses from the past or too far into the future.
        query = urllib.urlencode({'key' : 'TEST', 'minutesAfter' : '10', 'minutesBefore' : '0'})

        try:
                response = urllib.urlopen(base + query).read()
        except IOError as e:
		if attempts > 3:
			return False, 'Unable to open:  ' + base + query
		else:
			time.sleep(20)
			print 'checkArrivals sleeping'
			return(checkArrivals(apiURL, stop, arr, attempts+1))

        except urllib2.URLError, e:
                return False, "Timeout when opening:  " + base + query

        try:
                data = json.loads(response)
        except ValueError:
			return False, 'NO JSON Data in getStops: ' + base + query
        except error:
                return False, 'UNKNOWN ERROR in getStops' + base + query

        try:
                arrivals = data['data']['entry']['arrivalsAndDepartures']
        except KeyError:
                return False, 'Arrivals list not formatted as expected: ' + base + query

        for arrival in arrivals:
                # Check for number of predicted vs. scheduled arrivals
                if arrival['predicted']:
                        arr['predicted'] += 1

                        # Check for number of "perfect" predictions, i.e., predicted equals scheduled
                        if arrival['predictedArrivalTime'] == arrival['scheduledArrivalTime']:
                                arr['perfect'] += 1
                else:
                        arr['scheduled'] += 1
        return True, ""

#Check the OBA email to see if this code has been resolved.
#If it has, clear the alert and send an email to everyone on the Alert list.
def check_for_resolution(code, description):
	from datetime import datetime, timedelta
	import email
	from imapclient import IMAPClient

	ssl = True

	today = datetime.today()
	cutoff = today - timedelta(days=1)

        ## Connect, login and select the INBOX
	server = IMAPClient(HOST, use_uid=True, ssl=ssl)
	server.login(USERNAME, PASSWORD)
	select_info = server.select_folder('INBOX')

       ## Search for relevant messages
       ## see http://tools.ietf.org/html/rfc3501#section-6.4.5
	messages = server.search(
		['SINCE %s' % cutoff.strftime('%d-%b-%Y')])
	response = server.fetch(messages, ['RFC822'])

	target_subject = "Re: OBA Alert!: " + str(code) + '.'
	resolved = False
	for msgid, data in response.iteritems():
		msg_string = data['RFC822']
		msg = email.message_from_string(msg_string)
		subject =  msg['Subject']

		#Pulls the body of the solution email.
		body = ''
		for part in msg.walk():
			if part.get_content_type() == 'text/plain':
				body += str(part.get_payload()) + '\n'

		if subject == target_subject:
			resolved = True
			resolver = msg['From']
			time_resolved = msg['date']
			break
	if resolved:
		clear_alert(code, description)
		description = "OBA Alert: " + str(code) + ", " + description + "\nwas resolved by " + resolver + ' at ' + time_resolved + '.' 
		description += "\n\nSOLUTION:  " + body

		sendGmail(alert_list, description ,"OBA Alert Resolved!: " + str(code) + '.' )
		return True
	else:
		return False

def sendGmail(recipients, message, subject):

	FROM = from_address

        msg = MIMEMultipart()
        msg["From"] = FROM
        msg["Subject"] = subject
        msg['Date'] = formatdate(localtime=True)
        message1 = MIMEText(message, 'plain')
        msg.attach(message1)

        # The actual mail send
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.starttls()
        server.login(USERNAME,PASSWORD)

	for recipient in recipients:
		TO  = recipient
		server.sendmail(FROM, TO, msg.as_string())#.as_string())

        server.quit()

def clear_alert(code, description):

	#Update the status code in the alert_status.csv file
	status_file = open(csv_status_file, 'wb')
	status_array = []
	status_array.append({'status':0, 'code':code, 'description':description})
	fieldnames = ['status', 'code', 'description']
	writer = csv.DictWriter(status_file, delimiter=',', fieldnames=fieldnames)
	writer.writerow(dict((fn,fn) for fn in fieldnames))
	for row in status_array:
		writer.writerow(row)


def create_alert(description):
	#Get the previous code
	status_file = open(csv_status_file)
        reader = csv.DictReader(status_file)
	for row in reader:
		code =  int(row['code'])
		break
	status_file.close()
	code += 1

	#Send the relevant emails and texts
	sendGmail(alert_list, description ,"OBA Alert!: " + str(code) + '.' )

	#Update the status code in the alert_status.csv file
	status_file = open(csv_status_file, 'wb')
	status_array = []
	status_array.append({'status':1, 'code':code, 'description':description})
	fieldnames = ['status', 'code', 'description']
	writer = csv.DictWriter(status_file, delimiter=',', fieldnames=fieldnames)
	writer.writerow(dict((fn,fn) for fn in fieldnames))
	for row in status_array:
		writer.writerow(row)

def get_alert_status():
	"""
	get_alert_status checks a file called alert_status.csv.
	If the status of the file is a 1, then the system is in alert status waiting for a response
	If the status of this file is a 0, then the system is operating normally
	"""
	status_file = open(csv_status_file)
        reader = csv.DictReader(status_file)
	for row in reader:
		return int(row['status']), int(row['code']), row['description']

def main():
	#Check to see if an alert has already been sent but not addressed.
	#This will prevent duplcate alerts
	status, code, description = get_alert_status()
	minute = datetime.datetime.now().minute
	if status:
		resolved = check_for_resolution(code, description)
		if not resolved:
			return
	elif (minute%report_frequency) > 0: #if we are not in an alert, only run the test every 15 minutes
		return

        # Unique API URL (root)
        url = root_url

        # Limiting factor for number of stops to cycle through
        factor = 100

        result, agencies = getAgencies(url)
        if not result:
                report = agencies
                create_alert(report)
                return

        report = ""

        for agency in agencies:

                result, stops = getStops(url, agency)
                if not result:
                        report = stops
			create_alert(report)
                        continue

                lim = len(stops)/factor
                stopIndex = 0
                counts = {
                        'predicted' : 0,
                        'scheduled' : 0,
                        'perfect' : 0
                        }

                for stop in stops:
                        stopIndex += 1
                        result, message = checkArrivals(url, stop, counts)
                        if not result:
                                report = message
				create_alert(report)
                                break
                        if stopIndex > lim:
                                break

                #These are sanity checks for the various agencies.  They will only be run if the agency ID is in the realtime_agencies list
                if not(agency['agencyId'] in realtime_agencies):
                        print agency['agencyId'] + " is not included in the realtime test."
                elif datetime.datetime.now().hour < START_OF_DAY:
                        print 'It is before ' + START_OF_DAY + ' , dont send an alert'
                elif counts['predicted'] < counts['scheduled']:
			create_alert(agency['agencyId'] + " is batting < .500")
                elif counts['predicted'] + counts['scheduled'] == 0:
			create_alert(agency['agencyId'] + " is not returning any schedule or predicted times!")
		elif float(counts['perfect'])/float(counts['predicted']) > .9:
                        create_alert(agency['agencyId'] + " is reporting > 90% perfect predictions.")
		else:
                        print agency['agencyId'] + " is looking good."

                report += "\n\n" + agency['agencyId'] + "\n\nTrips with real-time: " + str(counts['predicted'])+ " of " + str(counts['scheduled'] + counts['predicted']) + "\nTrips without real-time: " + str(counts['scheduled'])+ " of " + str(counts['scheduled'] + counts['predicted']) + "\nPerfect predictions: " + str(counts['perfect']) + " of " + str(counts['scheduled'] + counts['predicted'])


        sendGmail(report_list, report, 'OBA Report')

if __name__ == '__main__':
    main()
