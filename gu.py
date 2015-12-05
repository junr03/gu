# Grading Utilities Module
import datetime
import pytz
import os
from lxml import etree
import re
import csv

def extract_account(tarname):
    return tarname.split('_')[0].split('-')[-1]

def extract_timestamp(tarname):
    date = map(int, tarname.split('_')[1].split('-'))
    time = map(int, tarname.split('_')[2].split('-'))
    return pytz.utc.localize(datetime.datetime(date[0], date[1], date[2],
                                               time[0], time[1], time[2]))

def deadline_in_utc(deadline):
    eastern = pytz.timezone('US/Eastern')
    deadline_eastern=eastern.localize(deadline)
    return deadline_eastern.astimezone(pytz.utc)

def get_latest_submission(path, partners=False):
    submissions = {}
    for submission in os.listdir(path):
        account = extract_account(submission)
        timestamp = extract_timestamp(submission)
        if account in submissions:
            if submissions[account][0] > timestamp:
                # we have the latest submission
                continue
        submissions[account] = [timestamp, submission]
    if partners:
        return divide_into_individuals(submissions)
    return submissions

def divide_into_individuals(submissions):
    divided_submissions = {}
    for account, information in submissions.iteritems():
        accounts = re.split('\d*', account)
        for i in range(0, len(accounts) - 1):
            divided_submissions[accounts[i]] = information
    return divided_submissions



def update_late_days(xml_path, deadline, submissions):
    """ Updates the late days of each student in the grades XML based on their
    submissions.
    """
    deadline_time = deadline.time()
    assignment_string = "06"
    one_hour = (deadline + datetime.timedelta(hours=1)).time()
    tree = etree.parse(xml_path)
    root = tree.getroot()
    for account, submission in submissions.iteritems():
        timestamp = submission[0]

        # did the student submit late?
        if deadline < timestamp:

            # determine if the student is within a time that incurs in grace period
            grace_period = False
            if (deadline_time < timestamp.time() and
               timestamp.time() < one_hour):
                grace_period = True

            late_days = 0
            # determine late days
            delta = timestamp - deadline
            if grace_period:
                late_days = delta.days
            else:
                late_days = delta.days + 1

            search = tree.xpath("./student/account[contains(text(), '{}')]".format(account))
            if len(search) == 0:
                print "Student {} had {} late days, and {} grace period".format(account, late_days, grace_period)
                print "Student: {} is not in XML".format(account)
                continue
            student_node = search[0].getparent()
            item = student_node.find("group[@name='Assignment']/item[@name='{}']".format(assignment_string))
            item.set('late','{}'.format(late_days))

            print "Student {} had {} late days, and {} grace period".format(account, late_days, grace_period)

    #TODO: change this to path when sure
    tree.write('output.xml')

def update_grades(csv_path, xml_path):
    """
    updates grades based on csv with email and total grade
    """
    grades = {}
    with open(csv_path, 'rbU') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
            grades[row[0]] = row[1]
    assignment_string = "06"
    tree = etree.parse(xml_path)
    root = tree.getroot()
    for account, grade in grades.iteritems():
        search = tree.xpath("./student/account[contains(text(), '{}')]".format(account))
        if len(search) == 0:
            print "Student {} had {} grade. NOT IN XML".format(account, grade)
            continue
        student_node = search[0].getparent()
        item = student_node.find("group[@name='Assignment']/item[@name='{}']".format(assignment_string))
        item.set('score','{}'.format(grade))

    #TODO: change this to path when sure
    tree.write('output.xml')




