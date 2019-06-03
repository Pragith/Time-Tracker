from pandas import DataFrame, read_csv, to_datetime
from datetime import datetime
import time, sys, os, argparse, pendulum

# Get report related arguments from the command line
parser = argparse.ArgumentParser()
parser.add_argument("-sd","--start_date", help="Enter date in YYYYMMDD format ONLY!", type=str)
parser.add_argument("-ed","--end_date", help="Enter date in YYYYMMDD format ONLY!", type=str)
parser.add_argument("-r","--report", help="Just leave it blank and current week's report will be generated", action='store_true')
#parser.add_argument("-ws","--week_start", help="Enter date in YYYYMMDD format ONLY!", type=str)
args = vars(parser.parse_args())

# Automatically retrieve the working directory
work_dir = os.path.dirname(os.path.realpath(__file__))

# Get the timesheet file path
timesheet_file = work_dir + r'\timesheet.csv'
last_record_file = work_dir + r'\last_record.csv' # This way it's faster to read the last task and write to the timesheet file without reading it completely

# Read the projects list
projects = read_csv(work_dir + r'\projects.csv')

# Get the last record in the timesheet
last_record = read_csv(last_record_file)
last_task = last_record.task.tolist()[0]
last_project = last_record.project.tolist()[0]

# Today
today = datetime.now().strftime("%Y-%m-%d")
now = time.time()


def list_projects():	
	id, project = projects['id'].tolist(), projects['project'].tolist()
	projects_list = [str(i) + '. ' + p for i,p in zip(id,project)]
	return print('\n'.join(projects_list))

def record_task(current_task, project_id):
	current_task = str(current_task) if current_task != '' else last_task # Same as previous task (If user entered blank)
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
	ts.to_csv(last_record_file, index=False)

def generate_report():
	timesheet = read_csv(timesheet_file, error_bad_lines=False)
	
	# Calculate the start and end dates of reports dynamically
	end = pendulum.now()	
	start = to_datetime(args['start_date']) if args['start_date'] else to_datetime(end.start_of('week').strftime('%Y-%m-%d'))
	end = to_datetime(args['end_date']) if args['end_date'] else to_datetime(end.strftime('%Y-%m-%d'))	
	timesheet['date'] = to_datetime(timesheet['date'])
	timesheet = timesheet[(timesheet['date'] >= start) & (timesheet['date'] <= end)]

	# Calculate efforts by day, project and task.
	timesheet = timesheet.groupby(['date','project','task'], group_keys=False).agg({'time':'count'}).reset_index()
	timesheet['hours'] = timesheet['time'] / 4
	timesheet['task'] = timesheet['task'].map(str) + ' (' + timesheet['hours'].map(lambda x: str(int(x)) if x.is_integer() else str(x)) + ')' 

	# Write the report to CSV
	if not os.path.exists('reports'):
		os.makedirs(work_dir + r'\reports')
	timesheet[['date','project','hours','task']].to_csv('reports/timesheet report - '+str(start.strftime('%d-%b-%Y'))+' to '+str(end.strftime('%d-%b-%Y'))+'.csv', index=False)
	timesheet[['date','project','hours','task']].to_csv('reports/timesheet report - latest.csv', index=False)
	
	print("Report generated for dates between {0} and {1}".format(start, end))


task_msg = """
######################
Enter current task: """
choice = 'report' if (args['report'] or args['start_date']) else 'task'
while choice != '':
	if choice == 'report':
		# Generate this week in review report
		generate_report()		
	else:
		# Enter current task
		print('Time now:',time.strftime("%H:%M",time.localtime(now)))
		print('Last task:',last_task)
		print('Last project:',last_project)		
		current_task = input(task_msg)		
		list_projects()		
		project_id = input("Select project: ")
		record_task(current_task, project_id)

	choice = ''
