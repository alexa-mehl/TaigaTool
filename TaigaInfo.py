import requests 
import json
import datetime
from datetime import timedelta
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.dates as mdates
import math

with open('config.json') as f:
    configData = json.load(f)

slug = configData['slug']
password = configData['password']
username = configData['username']
sprintNumber = configData['sprintNumber']
getUS = configData['plotUS']

# colors are used for team members
colors = ['blue', 'springgreen', 'orchid', 'navy', 'coral', 'olive', 'cyan']

http = 'https://api.taiga.io/api/v1/'

header = {'Content-Type': 'application/json'}

if username is not None:
	# header is only needed for private Taiga boards

	data ={'password': password,
			'type': 'normal',
			'username': username
	       }

	res = requests.post(http + '/auth', headers = header, data = json.dumps(data))
	test = res.json()
	token = test['auth_token']

	header = {'Content-Type': 'application/json', 
		  	  'Authorization': 'Bearer ' + token}



# goes through the US info provided in afer the Sprint call. This US Json
# does not contain the description and other main information. If it is needed then the API must
# be callse for each US. 
def getUSInfo():
	print('   These US are: ')

	for i in range(0,len(userStoriesJson)):
		created = datetime.datetime.strptime(userStoriesJson[i]['created_date'], '%Y-%m-%dT%H:%M:%S.%fZ')-timedelta(hours=7)
		usID = userStoriesJson[i]['id']
		userStories[usID] = {'name' : userStoriesJson[i]['subject'],
						  'created' : created,
						  'closed' : userStoriesJson[i]['is_closed'],
						  'points' : userStoriesJson[i]['total_points'],
						  'ref' : userStoriesJson[i]['ref'],
						  'tasks' : [],
						  'modified' : datetime.datetime.strptime(userStoriesJson[i]['modified_date'], '%Y-%m-%dT%H:%M:%S.%fZ')-timedelta(hours=7)
						}

		# request to get US histroy. Is used to see when the userstory was moved into the Spring. 
		res = requests.get(http +'history/userstory/'+str(usID), headers = header)
		userStories[usID]['userStoryHistory'] = res.json()

		US_H = userStories[usID]['userStoryHistory']

		# find when US was moved into this sprint
		for j in range(0,len(US_H)):
			if 'milestone' in US_H[j]['diff']:
				if (US_H[j]['diff']['milestone'][0] is None and US_H[j]['diff']['milestone'][1] == sprint['id']):
					userStories[usID]['inSprintDate'] = datetime.datetime.strptime(US_H[j]['created_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
					break;

		# print the collected information
		print('\n\n       ', userStories[usID]['name'])
		print('           US is done: ', userStories[usID]['closed'])
		print('           Created: ', userStories[usID]['created'].strftime(' %b %d %Y '))
		print('           Points: ', userStories[usID]['points'])
		print('           Put in Sprint: ', userStories[usID]['inSprintDate'].strftime(' %b %d %Y '))
		if userStories[usID]['inSprintDate'] > sprint['started']+ timedelta(days=1):
			print('           Put into Sprint after Sprint start ')

	userStories['None'] = {'name' : 'None',
							'tasks' : [],
							'ref' : 0}

# get project by slug
res = requests.get(http +'projects/by_slug', headers = header, params = {'slug' : slug})
projectInfo = res.json()
project_id = projectInfo['id']

project = {}

project['id'] = project_id
project['name'] = slug


# get members info for this project
res = requests.get(http +'memberships', headers = header, params = {'project' : project_id})
memberInfo = res.json()

# listing all members, saving member information in project
print('This project has ' + str(len(memberInfo)) + ' members. The members are: ')
members = {}
for i in range(0,len(memberInfo)):
	id = memberInfo[i]['user']
	if memberInfo[i]['full_name'] is not None:
		members[id] = {'name': memberInfo[i]['full_name'],
					 'role' : memberInfo[i]['role_name'],
					 'color' : colors[i],
					 'tasksNum' : 0,
					 'tasks' : []
					 }
		print(members[id]['name'] + ' : ' + members[id]['role'])

# adding one None member, so we can show tasks US not assigned to anyone. 
members['None'] = {'name': 'None',
				 'role' : 'None',
				 'color' : 'black',
				 'tasksNum' : 0,
				 'tasks' : []
				 }

# adding members to project
project['members'] = members
print('\n\n')

# get all sprints for the project info
res = requests.get(http + 'milestones', headers = header, params = {'project' : project_id})
sprintInfo = res.json()

sprints = {}

print('This project has ' + str(len(sprintInfo)) + ' sprints.')
for i in range(0,len(sprintInfo)):
	created = datetime.datetime.strptime( sprintInfo[i]['created_date'], '%Y-%m-%dT%H:%M:%S.%fZ')-timedelta(hours=7)
	startDate = datetime.datetime.strptime(sprintInfo[i]['estimated_start'], '%Y-%m-%d')
	endDate = datetime.datetime.strptime(sprintInfo[i]['estimated_finish'], '%Y-%m-%d')

	sprints[i] = {'name' : sprintInfo[i]['name'],
				  'created': created,
				  'started': startDate,
				  'endDate': endDate,
				  'totalPoints' : sprintInfo[i]['total_points'],
				  'closedPoints' : sprintInfo[i]['closed_points'],
				  'json' : sprintInfo[i],
				  'id' : sprintInfo[i]['id']
	}

	print(str(i), ':', sprints[i]['name'], '\n     Created: ', created.strftime(' %b %d %Y '), '\n     Start: ', startDate.strftime(' %b %d %Y '), '\n     End: ', endDate.strftime(' %b %d %Y '))
	print('     Closed/Created Points: ', sprints[i]['closedPoints'],'/', sprints[i]['totalPoints'])


project['sprints'] = sprints

if sprintNumber is None:
	sprintNumber = input('Choose a Sprint, type in the number mentioned for the sprint: ')
	type(sprintNumber)


# use a specific sprint from now on. 
sprint = sprints[int(sprintNumber)]


# go through all User Stories of the project
userStories = {}
userStoriesJson = sprint['json']['user_stories']

print('\n\nYou chose: ', sprint['name'])
print('   #US: ', len(userStoriesJson))

if getUS:
	getUSInfo()

data ={'project': project['id'],
		'milestone': sprint['id'],
		'page' : 1
    }

# get all tasks 
res = requests.get(http +'tasks', headers = header, params = data)
tasksJson = res.json()


if int(res.headers['x-pagination-count']) > 30:
	num = math.ceil(int(res.headers['x-pagination-count'])/30)
	for i in range(num-1):
		data['page'] = (i+2)
		res = requests.get(http +'tasks', headers = header, params = data)
		new = res.json()
		tasksJson = tasksJson + new


# print(len(tasksJson))

sprint['tasksJson'] = tasksJson

tasks = {}
for i in range(0,len(tasksJson)):
	created = datetime.datetime.strptime(tasksJson[i]['created_date'], '%Y-%m-%dT%H:%M:%S.%fZ')-timedelta(hours=7)
	if (tasksJson[i]['finished_date'] is None):
		finished_date =  None
	else:
		finished_date = datetime.datetime.strptime(tasksJson[i]['finished_date'], '%Y-%m-%dT%H:%M:%S.%fZ')-timedelta(hours=7)
	taskID = tasksJson[i]['id']
	tasks[taskID] = {'name' : tasksJson[i]['subject'],
				'ref' : tasksJson[i]['ref'],
				'created' : created,
				'finished' : finished_date,
				'is_closed' : tasksJson[i]['is_closed'],
				'assignedTo' : tasksJson[i]['assigned_to']
				}

	# Check if task belogs to a User Story or is not assigned
	if  tasksJson[i]['user_story_extra_info'] is not None:
		tasks[taskID]['usID'] = tasksJson[i]['user_story_extra_info']['id'] 
		tasks[taskID]['usName'] = tasksJson[i]['user_story_extra_info']['subject']
		userStories[tasksJson[i]['user_story_extra_info']['id']]['tasks'].append(tasks[taskID])
	else:
		tasks[taskID]['usID'] = 'None'
		tasks[taskID]['usName'] = 'None'
		userStories['None']['tasks'].append(tasks[taskID])
		
	# add the tasks to the member that has the task assigned
	if tasksJson[i]['assigned_to'] is None:
		name = 'None'
		members['None']['tasksNum'] = members['None']['tasksNum'] + 1
		members['None']['tasks'].append(taskID)
	else:
		name = members[tasksJson[i]['assigned_to']]['name']
		members[tasksJson[i]['assigned_to']]['tasksNum'] = members[tasksJson[i]['assigned_to']]['tasksNum'] + 1
		members[tasksJson[i]['assigned_to']]['tasks'].append(taskID)

print('################### US to Task ############################')
for usID in userStories:
	print("US: ", userStories[usID]['ref'], ' has ', len(userStories[usID]['tasks']), ' tasks.') 

# going through the tasks history and plotting the information
t = 0 # to give the y value in the plot
events = {} # tasks can have a number of events
# exit()

# go through history and start plotting. 
start = sprint['started']
stop = min([sprint['endDate'],datetime.datetime.now()])


date_list = [start + datetime.timedelta(days=x) for x in range(0, (stop-start).days)]

# create the plot window
fig, ax = plt.subplots(figsize=(8, 8))

# Create the base line (for whole sprint)
ax.plot((start, stop), (0, 0), 'k--', linewidth=1, alpha=.5, color = 'gray')

# using dates on X-Axis
ax.get_xaxis().set_major_formatter(mdates.DateFormatter('%m/%d'))
print('################### MEMBERS ############################')

# iterate through all members of the team (including None - unassigned)
for key in members:
	print('########################################################')
	print('\n' + members[key]['name'] + ' has '+ str(members[key]['tasksNum']) + ' tasks.')
	old_t = t

	# iterate through all tasks assigned to this user (at the moment the program is called)
	for i in range(0,len(members[key]['tasks'])):
		taskID =members[key]['tasks'][i]
		task = tasks[taskID]

		ax.plot((task['created'], stop), (t+1, t+1), 'k--', linewidth=0.5, alpha=.5)
		res = requests.get(http +'history/task/' + str(taskID), headers = header)
		taskHistory = res.json()

		task['history'] = taskHistory
		task['events'] = {}
		task['inProgressTime'] = stop - stop
		task['inTestingTime'] = stop - stop
		eventsS = []
		eventsA = []
		
		if (len(taskHistory)) > 0:
			print('\n Events: Task #' + str(task['ref']) + ' name: ' + task['name'])

		# interate through all history events of the task 
		for j in range(0, len(taskHistory)):
			history = taskHistory[j]
			diff = history['values_diff']
			eventS = {}
			eventA = {}

		 	# only status changes
			if 'status' in diff.keys():
				eventS['created'] = datetime.datetime.strptime(history['created_at'], '%Y-%m-%dT%H:%M:%S.%fZ')-timedelta(hours=7)
				eventS['status1'] = diff['status'][1]
				eventS['status0'] = diff['status'][0]
				print('     ', (eventS['created'].strftime(' %b %d %Y ')), ' ', diff['status'][1])

				# plotting the events
				if len(eventsS) > 0 :
					eS =  eventsS[len(eventsS)-1]['created']
				else:
					eS = task['created']

				if eventS['status0'] == 'In progress':
					ax.plot((eS, eventS['created']), (t+1, t+1), 'k', color = 'red', linewidth=6, alpha=.5)
					ax.plot((eS, eS), (t+1, t+1+0.1), 'k--', marker = '.', color = 'red', linewidth=1)
					task['inProgressTime'] =  task['inProgressTime'] + eventS['created'] - eS
				if eventS['status0'] == 'Ready for test':
					ax.plot((eS, eventS['created']), (t+1, t+1), 'k', color = 'orange', linewidth=3, alpha=.5)
					ax.plot((eS, eS ), (t+1, t+1+0.2), 'k--', marker = '.', color = 'orange', linewidth=1)
					task['inTestingTime'] = task['inTestingTime'] + eventS['created'] - eS
				if eventS['status0'] == 'Closed':
					ax.plot((eS, eventS['created']), (t+1, t+1), 'k', color = 'green', linewidth=3, alpha=.5)
					ax.plot((eS, eS), (t+1, t+1+0.3), 'k--', marker = '.', color = 'green', linewidth=1)
				eventsS.append(eventS)

			# only assignment changes
			if 'assigned_to' in diff.keys():
				eventA['created'] = datetime.datetime.strptime(history['created_at'], '%Y-%m-%dT%H:%M:%S.%fZ')-timedelta(hours=7)
				eventA['assigned'] = diff['assigned_to'][1]
				print('     ', eventA['created'].strftime(' %b %d %Y '), ' ', diff['assigned_to'][1])
				ax.plot((eventA['created'], eventA['created']), (t+1, t+1-0.3), 'k--', marker = '.', color =  members[key]['color'], linewidth=1)
				eventsA.append(eventA)

		# for the end of the sprint (or the currect time)
		length = len(eventsS) - 1 
		if len(eventsS) > 0: 
			length = len(eventsS) - 1
			if eventsS[length]['status1'] == 'Closed':
				ax.plot((eventsS[length]['created'], stop), (t+1, t+1), 'k', color = 'green', linewidth=3, alpha=.5)
				ax.plot((eventsS[length]['created'], eventsS[length]['created']), (t+1, t+1+0.3), 'k--', marker = '.', color = 'green', linewidth=1)
			if eventsS[length]['status1'] == 'Ready for test':
				task['inTestingTime'] = task['inTestingTime'] + stop - eventsS[length]['created']
				ax.plot((eventsS[length]['created'], stop), (t+1, t+1), 'k', color = 'orange', linewidth=3, alpha=.5)
				ax.plot((eventsS[length]['created'], eventsS[length]['created'] ), (t+1, t+1+0.2), 'k--', marker = '.', color = 'orange', linewidth=1)
			if eventsS[length]['status1'] == 'In progress':
				task['inProgressTime'] =  task['inProgressTime'] + stop - eventsS[length]['created']
				ax.plot((eventsS[length]['created'], stop), (t+1, t+1), 'k', color = 'red', linewidth=6, alpha=.5)
				ax.plot((eventsS[length]['created'], eventsS[length]['created']), (t+1, t+1+0.1), 'k--', marker = '.', color = 'red', linewidth=1)
			ax.text(stop+timedelta(hours=140), t+0.8 , '#'+ str(round(task['inProgressTime'].seconds/60/60 + task['inProgressTime'].days*24)), horizontalalignment='center', fontsize=8, color = 'red')
			ax.text(stop+timedelta(hours=185), t+0.8 , '#'+ str(round(task['inTestingTime'].seconds/60/60+ task['inTestingTime'].days*24)), horizontalalignment='center', fontsize=8, color = 'orange')
		ax.text(stop+timedelta(hours=70), t+0.75 , 'US#'+ str(userStories[task['usID']]['ref']) + ' #'+ str(task['ref']), horizontalalignment='center', fontsize=10)

		if len(eventsA) == 0:
			ax.plot((task['created'], task['created']), (t+1, t+1-0.3), 'k--', marker = '.', color =  members[key]['color'], linewidth=1)
				

		events['status'] = eventsS
		events['assigned_to'] = eventsA	
		task['events'] = events
		t = t + 1

	if(len(members[key]['tasks'])>0):
		ax.plot((start, start), (t+0.3, old_t+0.7), 'k', color = members[key]['color'], linewidth=3, alpha=.5)	
		ax.text(start- timedelta(days=5), old_t+0.7, members[key]['name'], horizontalalignment='center', fontsize=8, color = members[key]['color'])


ax.plot(stop+timedelta(hours=200), t+2)
ax.plot(start-timedelta(hours=200), t+2)

plt.show()

