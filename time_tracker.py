from pandas import DataFrame, read_csv, to_datetime
from datetime import datetime
import time, sys

config = read_csv('config.txt', sep=",")

# Get the timesheet file path
timesheet_file = config['timesheet_file'][0]

# Read project list
projects = read_csv(config['projects_file'][0])

# Last record
timesheet = read_csv(timesheet_file)
last_record = timesheet.tail(1)
last_task = last_record.task.tolist()[0] # Same as previous task (If user entered blank)
last_project = last_record.project.tolist()[0]

# Today
today = datetime.now().strftime("%Y-%m-%d")
now = time.time()


def list_projects():	
	id, project = projects['id'].tolist(), projects['project'].tolist()
	projects_list = [str(i) + '. ' + p for i,p in zip(id,project)]
	return print('\n'.join(projects_list))

def record_task(current_task, project_id):
	current_task = str(current_task) if current_task != '' else last_task
	project = projects[projects.id == int(project_id)]['project'].tolist()[0] if project_id != '' else last_project
	# Generate task record dataframe
	ts = DataFrame({
		'date':today,
		'time':now,
		'project': project,
		'task':current_task
		}, index=[0])
	# Push to csv
	ts.to_csv(timesheet_file, header=False, mode='a', index=False)

def generate_report(timesheet):
	import pendulum
	today = pendulum.now()
	#today = pendulum.datetime(2019, 4, 14, tz='America/Toronto')
	start = to_datetime(today.start_of('week').strftime('%Y-%m-%d'))
	today = to_datetime(today.strftime('%Y-%m-%d'))

	timesheet['date'] = to_datetime(timesheet['date'])
	timesheet = timesheet[(timesheet['date'] >= start) & (timesheet['date'] <= today)]

	timesheet = timesheet.groupby(['date','project','task'], group_keys=False).agg({'time':'count'}).reset_index()
	timesheet['hours'] = timesheet['time'] / 4
	timesheet['task'] = timesheet['task'].map(str) + ' (' + timesheet['hours'].map(lambda x: str(int(x)) if x.is_integer() else str(x)) + ')' 

	timesheet[['date','project','hours','task']].to_csv('timesheet_report_'+str(start.strftime('%d-%m-%Y'))+'.csv', index=False)
	return str(start.strftime('%d-%m-%Y'))

# Get user's choice
task_msg = """
######################
Enter current task: """

project_msg = "Select project: "


choice = sys.argv[1] if len(sys.argv) > 1 else 'task'
while choice != '':
	if choice == 'report':
		# Generate this week in review report		
		print("Report generated for week:",generate_report(timesheet))
	else:
		# Enter current task
		print('Time now:',time.strftime("%H:%M",time.localtime(now)))
		print('Last task:',last_task)
		print('Last project:',last_project)
		current_task = input(task_msg)		
		list_projects()		
		project_id = input(project_msg)
		record_task(current_task, project_id)

	choice = ''
