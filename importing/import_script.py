#!/usr/bin/python

import os
import sys
import csv
import fnmatch as fnmatch
from hashlib import md5
from collections import defaultdict

import numpy as np
from scipy.stats import stats  
from matplotlib.figure import Figure  # for plotting

# =========
# SETTINGS
# =========
django_dir = '/home/kevindunn/webapps/modelling3e4_grades'
app_dir    = '/home/kevindunn/webapps/modelling3e4_grades/grades/student'

# Categories for the course, as a list of 2-element tuples, containing the fraction of the grade 
course_categories = [   ('Tutorials', 0.1), 
                        ('Assignments', 0.2), 
                        ('Midterm: take-home', 0.1), 
                        ('Midterm: written', 0.15), 
                        ('Final exam', 0.45)
                    ]
                    
# How are the columns layed out in the spreadsheet?
column_layout = {'last_name': 0,
                 'first_name': 1,
                 'email_address': 2,
                 'student_number': 3,
                 'grad_student': 4,         # column can be left empty for undergraduates
                 'special_case': 5,         # must be "Yes" or blank.  If "Yes", then provide an entry in the ``manual_grades`` list below
                }
                
row_layout = {   'category': 0,             # must be spelt exactly like entries in ``course_categories``
                 'work_unit': 1,            # e.g. "Tutorial 1", or "Assignment 2"
                 'max_grades': 2,           # for the work unit. e.g. "3" or "[2,1]"  <---- used for [400,600] courses
                 'question_name': 3,        # e.g. "Question 1"
                 'max_question_grade': 4,   # for the question.  e.g. "3" or "[2,1]"  <---- used for [400,600] courses
             }

# Manual final grades (if required adjustment)
#                 ('FIRST',   'LAST',   'StudNum', Grade,  'email__@mcmaster.ca', GradStudent, Special_case)
manual_grades = [ ('GURVEER', 'DHANOA', '0655007', 72.785, 'dhanoag@mcmaster.ca', False,       True)]

sys.path.append(django_dir)
sys.path.append(app_dir)
os.environ['DJANGO_SETTINGS_MODULE'] = 'grades.settings'
from grades.student.models import Grade, Question, WorkUnit, Category, Student, GradeSummary, WorkUnitSummary, CategorySummary, Token
from django.contrib.auth.models import User

# TODO:
# * calculate the average grade for all work units in this category
# * leave NA's out of the bar plot calculation

def create_student_as_user(student_number, first_name, last_name, email):
    """ Create a new user with that student number, but watch incase the student already exists in the DB"""
    import sqlite3
    user = User(username=student_number, first_name=first_name, last_name=last_name, email=email, password='<it does not matter what we use here - it will be ignored>')
    user.is_staff = False
    user.is_superuser = False
    user.is_active = True
    try:
        user.save()    
    except sqlite3.IntegrityError:
        pass
        
def summary_string(data):
    """ Returns the string representation of the data in `vector` """
    summary = (np.nanmin(data), stats.scoreatpercentile(data,25), np.median(data), stats.scoreatpercentile(data,75), np.nanmax(data))
    return "[%s, %s, %s, %s, %s]" % summary

    
def create_image(data, image_type='default'):
    """
    Creates an image from the `data`, depending on the image_type.  
    
        image_type = 'assignment': creates an [alpha, beta, gamma, NA] barplot of counts
                                   data is expected to be a string, e.g. '80,23,12,9' (no brackets, just a comma separated string)
        image_type = 'default': creates a horizontal histogram from the np array in `data`
        
    Returns the string of the image
    """
    if not isinstance(data, basestring):
        data_string = data.tostring()
    else:
        data_string = data
    filename = md5(data_string+image_type).hexdigest() + '.png'
    if image_type.lower() == 'assignment':
        fig = Figure(figsize=(2,1))
        rect = [0.2, 0.20, 0.75, 0.80]  # Left, bottom, width, height
        ax = fig.add_axes(rect, frameon=False)

        alpha, beta, gamma, NA = [int(item) for item in data_string.split(',')]
        counts = [NA, gamma, beta, alpha]
        position = np.arange(4)+.5    # bar centers (y-axis)

        ax.barh(bottom=position, width=counts, align='center', color='blue', edgecolor="blue", linewidth=0)
        ax.yaxis.set_ticks(position)
        ax.set_yticklabels(( 'N/A', r'$\gamma$', r'$\beta$', r'$\alpha$'), fontsize=15)

        # No tick marks (does not remove the ticklabels!)
        ax.xaxis.set_ticks_position('bottom')
        ax.yaxis.set_ticks_position('left')
        #ax.xaxis.set_ticks([0, 45, 90])
        #ax.set_xticklabels(('0', '45', '90'), fontsize=13)
        max_tick = int(np.ceil(np.max(counts)/10.0)*10.0)
        ax.xaxis.set_ticks([0, max_tick])
        ax.set_xticklabels(('0', str(max_tick)), fontsize=13)

        # Grid lines
        ax.grid(color='r', linestyle='-.', linewidth=1)
        for grid in ax.yaxis.get_gridlines():
            grid.set_visible(False)

        from matplotlib.backends.backend_agg import FigureCanvasAgg
        canvas=FigureCanvasAgg(fig)
        fig.savefig(filename, dpi=300, facecolor='w', edgecolor='w', orientation='portrait', papertype=None, format=None, transparent=True)
        
    if image_type.lower() == 'default':
        mind, maxd = np.nanmin(data), np.nanmax(data)
        fig = Figure(figsize=(2,1))
        rect = [0.2, 0.20, 0.75, 0.70]  # Left, bottom, width, height
        ax = fig.add_axes(rect, frameon=False)
        
        n, bins, patches = ax.hist(data[np.isfinite(data)], bins=10, range=None, normed=False, cumulative=False, bottom=None, histtype='bar', align='mid', 
                            orientation='horizontal', rwidth=None, log=False, color='blue', edgecolor="blue", linewidth=0)
        ax.yaxis.set_ticks([mind, maxd])
        ax.set_yticklabels((str(mind), str(maxd)), fontsize=13)

        # No tick marks (does not remove the ticklabels!)
        ax.xaxis.set_ticks_position('bottom')
        ax.yaxis.set_ticks_position('left')
        max_tick = int(np.ceil(np.max(n)/10.0)*10.0)
        ax.xaxis.set_ticks([0, max_tick])
        ax.set_xticklabels(('0', str(max_tick)), fontsize=13)
        
        # Grid lines
        ax.grid(color='r', linestyle='-.', linewidth=1)
        for grid in ax.yaxis.get_gridlines():
            grid.set_visible(False)

        from matplotlib.backends.backend_agg import FigureCanvasAgg
        canvas=FigureCanvasAgg(fig)
        fig.savefig(filename, dpi=300, facecolor='w', edgecolor='w', orientation='portrait', papertype=None, format=None, transparent=True)
    return filename

def process_csvfile(csvf, skip_header_rows=5, skip_header_columns=6):
    """ Only creates the students from the CSV file 
    """
    index = 0
    headers = []
    grading = []
    
    # Split the rows in teh CSV:  the first few rows are "headers", the rest are grades for the students
    for row in csvf:
        if index < skip_header_rows:
            headers.append(row)
            index += 1
        else:
            grading.append(row)
    
    # Create the categories
    # Example: Category.objects.get_or_create(name="In-class quizzes", fraction=0.05)
    for entry in course_categories:
        Category.objects.get_or_create(name=entry[0], fraction=entry[1])
    
    
    # Manual override for manual final-grade 
    # Example: Student.objects.get_or_create(  first_name = 'GURVEER', last_name='DHANOA', student_number = '0655007', 
    #                                    manual_grade=72.785,  email_address = 'dhanoag@mcmaster.ca', has_password=False, grad_student=False, special_case=True)
    for override in manual_grades:
         Student.objects.get_or_create( first_name=override[0], 
                                        last_name=override[1],
                                        student_number=override[2],
                                        manual_grade=override[3],
                                        email_address=override[4],
                                        has_password=False,
                                        grad_student=override[5],
                                        special_case=override[6]
                                      )    
    for student in grading:
        # First create the student, if they don't already exist:
        last_name = student[column_layout['last_name']].strip()
        first_name = student[column_layout['first_name']].strip()
        email_address = student[column_layout['email_address']].strip() + '@mcmaster.ca'
        student_number = student[column_layout['student_number']].strip()
        if len(student_number) == 6:
            student_number = '0' + student_number
        has_password = False
        grad_student = student[column_layout['grad_student']].strip() == '600'
        special_case = student[column_layout['special_case']].strip() == 'Yes'
        Student.objects.get_or_create(first_name = first_name,
                        last_name=last_name,
                        student_number = student_number,
                        email_address = email_address,
                        has_password = has_password,
                        grad_student = grad_student,
                        special_case = special_case
                        )
                        
        # Create a user name for the student in the Django site: this is used later for authentication
        create_student_as_user(student_number, first_name, last_name, email_address)
        
    #Create any new work units (the Category to which the WorkUnit belongs must already exist)
    for index, entry in enumerate(headers[row_layout['work_unit']]):
        if entry:
            category = headers[row_layout['category']][index]
            max_grades = headers[row_layout['max_grades']][index].split(',')
            if len(max_grades) > 1:
                max_grade_400 = float(max_grades[0][1:])
                max_grade_600 = float(max_grades[1][0:-1])
            else:
                max_grade_400 = max_grade_600 = float(max_grades[0])
            WorkUnit.objects.get_or_create( name=entry, 
                                            max_grade_400=max_grade_400, 
                                            max_grade_600=max_grade_600, 
                                            category=Category.objects.filter(name=category)[0])
            
    #Create any new questions (the Work_unit to which it belongs must already exist - previous step)
    for index, entry in enumerate(headers[row_layout['question_name']]):  
        
        # Won't deal with any columns where the question name is empty
        if entry:
            work_unit = headers[row_layout['work_unit']][index]
            max_question_grade = headers[row_layout['max_question_grade']][index].split(',') 
            if len(max_question_grade) > 1:
                max_grade_400 = float(max_question_grade[0][1:])
                max_grade_600 = float(max_question_grade[1][0:-1])
            else:
                max_grade_400 = max_grade_600 = float(max_question_grade[0])
            q, created = Question.objects.get_or_create(name=entry, 
                                                        max_grade_400=max_grade_400, 
                                                        max_grade_600=max_grade_600, 
                                                        workunit=WorkUnit.objects.filter(name=work_unit)[0])
            
            print entry
            
            # Import all the grades, going along the columns:
            for row in grading:
                student_number = row[column_layout['student_number']].strip()
                if len(student_number) == 6:
                    student_number = '0' + student_number
                student_object = Student.objects.filter(student_number=student_number)[0] 
                grade_string = row[index]
                if grade_string == '':
                    Grade.objects.get_or_create(grade=None, student=student_object, question=q)
                elif grade_string in ('a', 'b', 'g'):
                    Grade.objects.get_or_create(grade_char=grade_string, student=student_object, question=q)
                else:
                    Grade.objects.get_or_create(grade=float(grade_string), student=student_object, question=q)
                    
    # For every student, and for every question, calculate that student's grade, then compute a summary of that question
    students = Student.objects.all()
    n_students = len(students)
    
    for category in Category.objects.all():                         # for every category e.g. "Assignments"
        for workunit in category.workunit_set.get_query_set():      # for every work unit in that category  # e.g. "Assignment 1"
            
            questions_in_wu = workunit.question_set.get_query_set()
            n_questions_per_wu = len(questions_in_wu)
            grade_matrix = np.zeros((n_students, n_questions_per_wu)) * np.NaN
            student_grade = np.zeros((n_students, 1)) 
            
            for col, question in enumerate(questions_in_wu):        # for every question in that work unit
                level_alpha = 0
                level_beta = 0
                level_gamma = 0
                level_NA = 0
                for row, student in enumerate(students):
                    student_wu_grade = 0.0
                    grade_item = Grade.objects.filter(question=question, student=student)[0]    
                    
                    # The maximum grade is the higher of either one; since 400 students are awarded 600-level grades
                    # if they attempt those questions
                    student_max_question_grade = max(question.max_grade_600, question.max_grade_400)
                    if grade_item.grade is None:
                        if grade_item.grade_char is None:
                            level_NA += 1
                            student_wu_grade = np.NaN
                        else:
                            if grade_item.grade_char == 'a':
                                student_wu_grade = 1.00 * student_max_question_grade
                                level_alpha += 1
                            elif grade_item.grade_char == 'b':
                                student_wu_grade = 0.75 * student_max_question_grade
                                level_beta += 1
                            elif grade_item.grade_char == 'g':
                                student_wu_grade = 0.50 * student_max_question_grade
                                level_gamma += 1
                    else:
                        student_wu_grade = grade_item.grade
                
                    grade_matrix[row, col] = student_wu_grade
                    student_grade[row, 0] += student_wu_grade
                    
                # We've got all the student grades for this question, now compute the summary (just for that question) 
                if category.name == 'Assignments':
                    counts = '%s,%s,%s,%s' % (level_alpha, level_beta, level_gamma, level_NA)
                    url_string = create_image(counts, image_type='assignment')
                    GradeSummary.objects.get_or_create(question=question, levels=4, level_names="['alpha', 'beta', 'gamma', 'N/A']", level_counts=counts, url_string=url_string)
                else:
                    summary_str = grade_matrix[:, col]
                    url_string = create_image(summary_str)
                    GradeSummary.objects.get_or_create(question=question, levels=0, summary_str=summary_string(summary_str), url_string=url_string)
                    
            # Go through the student list again to get their grade for that workunit, summarize that grade vector 
            for row, student in enumerate(students):
                if student.grad_student:
                    workunit_max_grade = workunit.max_grade_600
                else:
                    workunit_max_grade = workunit.max_grade_400

                student_grade[row, 0] = student_grade[row, 0] / float(workunit_max_grade) * 100

            summary_str = student_grade
            url_string = create_image(summary_str)      
            WorkUnitSummary.objects.get_or_create(workunit=workunit, summary_str=summary_string(summary_str), url_string=url_string)
            
        # Next, calculate the average grade for all work units in this category (later): use the class template below
        CategorySummary.objects.get_or_create(category=category, summary_str="STILL TO COME", url_string="NoneYet")
 
if __name__ == '__main__':
    for path, dirs, files in os.walk(os.getcwd()):
        for csvfile in [f for f in files if fnmatch.fnmatch(f, '*.csv')]:
            fullfile = os.path.abspath(os.path.join(path, csvfile))
            process_csvfile(csv.reader(open(fullfile)), skip_header_rows=5, skip_header_columns=6)



