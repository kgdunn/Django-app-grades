#!/usr/local/bin/python2.6
import sys, os
from collections import defaultdict
import numpy as np

sys.path.extend(['/home/kevindunn/webapps/modelling3e4_grades/'])
sys.path.extend(['/home/kevindunn/webapps/modelling3e4_grades/grades'])
sys.path.extend(['/home/kevindunn/webapps/modelling3e4_grades/grades/student'])
os.environ['DJANGO_SETTINGS_MODULE'] = 'grades.settings'

from grades.student.models import Student, Grade, Question, WorkUnit, Category, GradeSummary, WorkUnitSummary, CategorySummary, Token

def convert_percentage_to_letter(grade):
   
    if grade >= 0.0:
        letter = 'F'
        
    if grade >= 50.0:
        letter = 'D-'
    if grade >= 53.0:
        letter = 'D'
    if grade >= 57.0:
        letter = 'D+'
        
    if grade >= 60.0:
        letter = 'C-'
    if grade >= 63.0:
        letter = 'C'
    if grade >= 67.0:
        letter = 'C+'
        
    
    if grade >= 70.0:
        letter = 'B-'
    if grade >= 73.0:
        letter = 'B'
    if grade >= 77.0:
        letter = 'B+'
        
    if grade >= 80.0:
        letter = 'A-'
    if grade >= 85.0:
        letter = 'A'
    if grade >= 90.0:
        letter = 'A+'
    
    return letter

def calculate_assignment_grade(grade_list=None, best_n=5):
    """ Calculates the best N assignments out of the total number of assignments (2010).  
    Assignments not handed in are counted as 0.0.
    
    Returns a tuple: (list of top N assignments, average of the top N assignments)
    """
    grades = np.array(grade_list)
    best = np.sort(grades)[len(grades)-best_n:]
    return(best, np.mean(best))
    
def calculate_tutorial_grade(grade_list=None):
    """ Calculates the average of all tutorials.   Tutorials not handed in are counted as 0.0.

    Returns a tuple: (list of top N assignments, average of the top N assignments)
    """
    return np.mean(np.array(grade_list))
    
def get_workunit_list(student_number, categories):
    """ 
    Workunit = e.g. Assignment 4
    
    Also receives a list, `categories` = [
           {'name': 'Assignments',         'grade': NA,  'weight': 0.20,  'summary': 'URL1'},
           {'name': 'In-class quizzes ',   'grade': NA,  'weight': 0.05,  'summary': 'URL2'},
           {'name': 'Mini-project',        'grade': NA,  'weight': 0.10,  'summary': 'URL4'},
           {'name': 'Overall exam',        'grade': NA,  'weight': 0.25,  'summary': 'URL5'},
           {'name': 'Midterm',             'grade': NA,  'weight': 0.15,  'summary': 'URL3'}, ....]
    
    Fill in the 'grade' key in the WorkUnit dictionary for the student.    
    
    Return `workunits` is a list that is sent to the template.  Entries in the list are dictionaries.
    The template expects 4 keys in each dictionary: 
          `name`: the name of the work unit (e.g. Assignment 1, Written midterm, etc)
          `cattype`: the category to which the work unit belongs (e.g. "Assignments", "Midterm", "Project", etc)
          `maxgrade`: a string [400, 600] which contains the 400 and 600 level maximum available grade for the workunit
          `grade`: the student's actual grade for this work unit
          `summary`: a URL to an image that summarizes the class performance for this work unit
    """
    from time import time 
    t=time()
    workunits = []
    
    for wu_item in WorkUnit.objects.all():
        max_grade = '['+ str(wu_item.max_grade_400) + ', ' + str(wu_item.max_grade_600)  + ']'
        grad_student = Student.objects.filter(student_number=student_number)[0].grad_student
        if grad_student:
            student_max_wu_grade = wu_item.max_grade_600
        else:
            student_max_wu_grade = wu_item.max_grade_400
    
        student_wu_grade = 0.0
        for grade_item in Grade.objects.select_related().filter(student=student_number):
            wuname = grade_item.question.workunit.name
            
            # Only count that grade if it is part of the current work unit
            if wuname == wu_item.name:
                # if they attempt those questions
                student_max_question_grade = max(grade_item.question.max_grade_600, grade_item.question.max_grade_400)
                if grade_item.grade is None:
                    if grade_item.grade_char is None:
                        pass # If no grade; then no marks are awarded
                    else:
                        if grade_item.grade_char == 'a':
                            student_wu_grade += 1.00 * student_max_question_grade
                        elif grade_item.grade_char == 'b':
                            student_wu_grade += 0.65 * student_max_question_grade
                        elif grade_item.grade_char == 'g':
                            student_wu_grade += 0.40 * student_max_question_grade
                else:
                    student_wu_grade += grade_item.grade
          
        # Now that all questions (grades) have been added up for that work unit, compute 
        # the final grade for that work unit
        student_wu_grade = student_wu_grade / float(student_max_wu_grade) * 100
        student_wu_grade_str = str(round(student_wu_grade,1))

        workunits.append({'name': wu_item.name, 
                          'cattype': wu_item.category.name, 
                          'maxgrade': max_grade, 
                          'grade': student_wu_grade_str, 
                          'grade_numeric': student_wu_grade, 
                          'summary': 'Summary coming soon'})
    
    # Process each category for the student
    final_grade = 0.0
    for catdict in categories:
        cat_name = catdict['name']
        cat_weight = catdict['weight']
        catdict['grade'] = 0.0
        
        cat_grade = 0.0        
        if cat_name == 'Assignments':
            assignment_grade_list = []
            for entry in workunits:
                if entry['cattype'] == 'Assignments':
                    assignment_grade_list.append(entry['grade_numeric'])   
            catdict['best_assignments'], cat_grade = calculate_assignment_grade(assignment_grade_list)

        elif cat_name == 'Tutorials':
            tutorial_grade_list = []
            for entry in workunits:
                if entry['cattype'] == 'Tutorials':
                    tutorial_grade_list.append(entry['grade_numeric'])   
            cat_grade = calculate_tutorial_grade(tutorial_grade_list)

        else:
            for entry in workunits:
                if entry['cattype'] == cat_name:
                    cat_grade += entry['grade_numeric']
                    
        catdict['grade'] = cat_grade
                
        # Sum up the final grade      
        my_logger.debug('Cat=' + cat_name +'; weight=' + str(cat_weight) + '; grade=' +str(cat_grade))
        final_grade += cat_weight*cat_grade
                
    
    return  categories, final_grade
    
def process_student(student_number):
    """
    Get the grades for the student
    """
    the_student = Student.objects.get(student_number=student_number)
            
    if the_student.grad_student:
        level = '600'
    else:
        level = '400'
    student = {'name': the_student.first_name + ' ' + the_student.last_name,
               'lastname': the_student.last_name,
               'level': level, 
               'number': student_number, 
               'email': the_student.email_address, 
               'special': the_student.special_case}

    categories = []
    for item in Category.objects.all():
        categories.append({'name': item.name, 'weight': item.fraction, 'grade': 'N/A', 'maxgrade': str(int(item.fraction*100)) + '%', 'summary': 'Summary coming soon'})

    categories, final_grade = get_workunit_list(student_number = student_number, categories=categories)
        
    if the_student.special_case:
        student['final_grade'] = the_student.manual_grade
    else:
        student['final_grade'] = final_grade  
        
    # Rounding to the second decimal place: e.g. 76.98 is actually a B, but rounded to 1 decimal place, that's a 77% average, with a B+.
    student['final_grade'] = np.round(student['final_grade'], 1)
    

    return student
    
def process_all_students():
    """ 
    Gets a list of all students, calculates their grades, shows the list and makes a CSV file
    """
    all_students = Student.objects.all()
    output = {}
    lastnames = []
    grade_letters = defaultdict(int)
    for student in all_students:
        result = process_student(student.student_number)
        letter_grade = convert_percentage_to_letter(result['final_grade'])
        grade_letters[letter_grade] += 1
        output[result['lastname']] = '%0.50s: %0.7s: %0.2f: %0.3s:' % (result['name'], result['number'], result['final_grade'], letter_grade)
        lastnames.append(result['lastname'])
        print(output[result['lastname']])
    
    for student in sorted(lastnames):
        print(output[student])

    print(grade_letters)

if __name__ == '__main__':
    process_all_students()

