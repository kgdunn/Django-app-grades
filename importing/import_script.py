#!/usr/bin/python

import csv
import md5 as md5
from collections import defaultdict
import fnmatch as fnmatch
import numpy as np
from scipy.stats import stats  
from matplotlib.figure import Figure  # for plotting

import sys, os
sys.path.extend(['/var/django-projects/'])
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
    filename = md5.md5(data_string+image_type).hexdigest() + '.png'
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
    for row in csvf:
        if index < skip_header_rows:
            headers.append(row)
            index += 1
        else:
            grading.append(row)
    
    # Create the categories manually      
    Category.objects.get_or_create(name="Assignments", fraction=0.2)
    Category.objects.get_or_create(name="In-class quizzes", fraction=0.05)
    Category.objects.get_or_create(name="Mini-project", fraction=0.1)
    Category.objects.get_or_create(name="Midterm: take-home", fraction=0.15)
    Category.objects.get_or_create(name="Midterm: written", fraction=0.15)
    Category.objects.get_or_create(name="Final: take-home", fraction=0.15)
    Category.objects.get_or_create(name="Final: written", fraction=0.25)
    
    Student.objects.get_or_create(  first_name = 'GURVEER', last_name='DHANOA', student_number = '0655007', 
                                    manual_grade=72.785,  email_address = 'dhanoag@mcmaster.ca', has_password=False, grad_student=False, special_case=True)
    Student.objects.get_or_create(  first_name = 'BONOLO', last_name='MOKENTI', student_number = '0569803', 
                                    manual_grade=62.685,  email_address = 'mokentb@mcmaster.ca', has_password=False, grad_student=False, special_case=True)
    Student.objects.get_or_create(  first_name = 'SOCRAT', last_name='SALMAN', student_number = '0642589', 
                                    manual_grade=90.2725,  email_address = 'salmas2@mcmaster.ca', has_password=False, grad_student=False, special_case=True)
    Student.objects.get_or_create(  first_name = 'SAIF', last_name='MANKO', student_number = '0569807', 
                                    manual_grade=86.38,  email_address = 'mankos@mcmaster.ca', has_password=False, grad_student=False, special_case=True)
    Student.objects.get_or_create(  first_name = 'GHAJANIYA', last_name='VIJAYENTHIRAN', student_number = '0646777', 
                                    manual_grade=80.44,  email_address = 'vijayeg@mcmaster.ca', has_password=False, grad_student=False, special_case=True)
  

    for student in grading:
        # First create the student, if they don't already exist:
        last_name = student[0].strip()
        first_name = student[1].strip()
        email_address = student[2].strip() + '@mcmaster.ca'
        student_number = student[3].strip()
        has_password = False
        grad_student = student[4].strip() == '600'
        special_case = student[5].strip() == 'Yes'
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
        
    #Create any new work units (the Category to which the WorkUnit belongs must already exist: use the Admin Interface to create it!)
    for index, entry in enumerate(headers[1]):
        if entry:
            category = headers[0][index]
            max_grades = headers[2][index].split(',')
            max_grade_400 = float(max_grades[0][1:])
            max_grade_600 = float(max_grades[1][0:-1])
            WorkUnit.objects.get_or_create(name=entry, max_grade_400=max_grade_400, max_grade_600=max_grade_600, category=Category.objects.filter(name=category)[0])
            
    #Create any new work units (the Category to which the WorkUnit belongs must already exist: use the Admin Interface to create it!)
    for index, entry in enumerate(headers[3]):
        if entry:
            work_unit = headers[1][index]
            max_grades = headers[4][index].split(',')
            max_grade_400 = float(max_grades[0][1:])
            max_grade_600 = float(max_grades[1][0:-1])
            q, created = Question.objects.get_or_create(name=entry, max_grade_400=max_grade_400, max_grade_600=max_grade_600, workunit=WorkUnit.objects.filter(name=work_unit)[0])
            
            print entry
            
            # Import all the grades, going along the columns:
            for row in grading:
                student_number = row[3].strip()
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



