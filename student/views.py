from django.template import loader, Context
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.contrib import auth
from django.contrib.auth.models import User
from django.db.models import F
from django.core.context_processors import csrf
import numpy as np

# Logging
LOG_FILENAME = '/home/kevindunn/webapps/modelling3e4_grades/grades/django-log.log'
import logging.handlers
my_logger = logging.getLogger('MyLogger')   
my_logger.setLevel(logging.DEBUG)
fh = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=5000000, backupCount=5)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
fh.setFormatter(formatter)
my_logger.addHandler(fh)
my_logger.debug('A new call to the views.py file')

from grades.student.models import Student, Grade, Question, WorkUnit, Category, GradeSummary, WorkUnitSummary, CategorySummary, Token

# TODO: 
# Check email sending back to smtplib alone


# Settings
website_base = 'http://stats4.eng.mcmaster.ca/grades/tokens/'
media_prefix = '/media/'        # where the summary PNG files are stored
email_server = 'univmail.cis.mcmaster.ca'
email_port   = 25
email_username = 'dunnkg'
email_password = 'DrAD4dra'
token_length = 42

def generate_random_token(base_address):
    import random
    token = ''.join([random.choice('ABCEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz2345689') for i in range(token_length)])
    return base_address + token

def email_token_to_student(to_address, token_address):
    """ Sends an email to the student with the web address to log in."""
    
    message = '''\
From: dunnkg@mcmaster.ca
Subject: Web address to access 4C3/6C3 grades

This message has been sent, at your request, to retrieve your grades for the course CHE4C3/6C3.

The web address will only work once: ''' + token_address + '''\

You can re-request your grades as many times as you like.  There is no need to log in or log out afterwards - just close the web page.

The http://stats4.eng.mcmaster.ca web server.
'''

    import email, smtplib   
    sender = "dunnkg@mcmaster.ca"
    m = email.message_from_string(message)
    m.set_charset('iso-8859-1')
    #m['to'] = 'kgdunn@gmail.com'
    #m['from'] = 'dunnkg@mcmaster.ca'
    s = smtplib.SMTP()
    s.connect(email_server, port=email_port)
    s.login(user=email_username, password=email_password)
    
    out = s.sendmail(sender, to_address, m.as_string())
    s.quit()
    if len(out) == 0:
        my_logger.debug('Email sent successfully to student: ' + to_address)
        return True
    else:
        return False
        
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
                            student_wu_grade += 0.75 * student_max_question_grade
                        elif grade_item.grade_char == 'g':
                            student_wu_grade += 0.50 * student_max_question_grade
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

        else:
            for entry in workunits:
                if entry['cattype'] == cat_name:
                    cat_grade += entry['grade_numeric']
                    
        catdict['grade'] = cat_grade
                
        # Sum up the final grade      
        #my_logger.debug('Cat=' + cat_name +'; weight=' + str(cat_weight) + '; grade=' +str(cat_grade))
        final_grade += cat_weight*cat_grade
                
    my_logger.debug("Time to process student's grades = " + str(time()-t))
    return workunits, categories, final_grade
    
def generic_error(request):
    """ Returns this when an error occurs"""
    t = loader.get_template("generic_error.html")
    c = Context({})
    return HttpResponse(t.render(c))
    
def not_registered_sign_in(request):
    """ Invalid student number received"""
    t = loader.get_template("not_registered_sign_in.html")
    c = Context({})
    return HttpResponse(t.render(c))

def sent_email_sign_in(request):
    """ Sends an email to the user """
    my_logger.debug('Will send the user an email')
    t = loader.get_template("sent_email_sign_in.html")
    c = Context()
    return HttpResponse(t.render(c))

def process_token(request, token):
    """
    Returns the web-page for the student if the token is valid
    """
    my_logger.debug('About to process received token: ' + token)
    token_item = Token.objects.filter(token_address=website_base+token)

    if len(token_item) == 0:
        # Invalid token
        my_logger.debug('Invalid token received: ' + token)
        t = loader.get_template("invalid_token.html")
        c = Context({})
        return HttpResponse(t.render(c))
    elif token_item[0].has_been_used:
        # Used token
        my_logger.debug('Used token received: ' + token)
        t = loader.get_template("token_has_expired.html")
        c = Context({})
        return HttpResponse(t.render(c))
    else:
        # Valid taken
        student_number = token_item[0].student.student_number
        
        # Method 1 to update the record
        #t_updated = Token(token_item[0].id, has_been_used=True, token_address=token_item[0].token_address, student=token_item[0].student)
        #t_updated.save()
        
        # Method 2 to update the record
        token_item[0].has_been_used = not(F('has_been_used'))
        token_item[0].save()
        
        the_student = Student.objects.get(student_number=student_number)
        my_logger.debug('Deactivated token; verified ' + the_student.first_name + ' ' + the_student.last_name + ': showing grades')
                
        if the_student.grad_student:
            level = '600'
        else:
            level = '400'
        student = {'name': the_student.first_name + ' ' + the_student.last_name,
                  'level': level, 'number': student_number, 'email': the_student.email_address, 'special': the_student.special_case}

        # Part 1, categories (e.g. Assignments, Midterm, Project, Final exam)
        # `categories` is a list that is sent to the template.  Entries in the list are dictionaries.
        # The template expects 4 keys: 
        #       `name`: the name of the category (e.g. "Assignments", "Midterm", "Project", etc)
        #       `maxgrade`: the grade (out of 100%) which that category counts to the final mark
        #       `grade`: the actual grade the student achieved
        #       `summary`: a URI to an image (PNG) file that shows how the student performed relative to the class
        # categories = [{'name': 'Assignments',         'grade': 18,  'maxgrade': 20,  'summary': 'URL1'},
        #           {'name': 'In-class quizzes ',   'grade':  5,  'maxgrade':  5,  'summary': 'URL2'},
        #           {'name': 'Mini-project',        'grade':  7,  'maxgrade': 10,  'summary': 'URL4'},
        #           {'name': 'Overall exam',        'grade': 25,  'maxgrade': 25,  'summary': 'URL5'},
        #           {'name': 'Midterm',             'grade': 17,  'maxgrade': 15,  'summary': 'URL3'},
        #          ]
        categories = []
        for item in Category.objects.all():
            categories.append({'name': item.name, 'weight': item.fraction, 'grade': 'N/A', 'maxgrade': str(int(item.fraction*100)) + '%', 'summary': 'Summary coming soon'})

        # Part 2, work units (e.g. assignment 4)
        workunits, categories, final_grade = get_workunit_list(student_number = student_number, categories=categories)
        
        if the_student.special_case:
            student['final_grade'] = the_student.manual_grade
        else:
            student['final_grade'] = final_grade  

	# Rounding to one decimal place: e.g. 76.98 is actually a B, but rounded to 1 decimal place, that's a 77% average, with a B+.
	student['final_grade'] = np.round(student['final_grade'], 1)

        student['final_grade_letter'] = convert_percentage_to_letter(student['final_grade'])

        my_logger.debug('Final grade for ' + the_student.first_name + ' ' + the_student.last_name + ': ' + str(student['final_grade']) + '; reported as: ' + student['final_grade_letter'])

        # Part 3, grades (e.g. Question 2 in Assignment 4)
        #         Extra complexity here is to account for assignment grades vs midterm grades
        grades = []
        for item in Grade.objects.select_related().filter(student=student_number):
            question_name = item.question.name
            wuname = item.question.workunit.name
            max_grade = '['+ str(item.question.max_grade_400) + ', ' + str(item.question.max_grade_600)  + ']'
            # How did the whole class perform on this question?
            rest_of_class = GradeSummary.objects.filter(question=item.question)[0]
            if item.grade is None:
                if item.grade_char is None:
                    grade_str = 'N/A'
                else:
                    if item.grade_char == 'a':
                        grade_str = '&alpha;'
                    elif item.grade_char == 'b':
                        grade_str = '&beta;'
                    elif item.grade_char == 'g':
                        grade_str = '&gamma;'
            else:
                grade_str = str(item.grade)
                
            # TODO: level_names="['alpha', 'beta', 'gamma', 'N/A']", level_counts = 23,13,2,53
            # Make an alt string for the image from these entities
            grades.append({'name': question_name, 'wuname': wuname, 'maxgrade': max_grade, 'grade': grade_str, 'summary': media_prefix+rest_of_class.url_string})
        
        # Send the 3 parts to the template for rendering to HTML
        t = loader.get_template("display_grades.html")
        c = Context({'Category': categories, 'WorkUnit': workunits, 'Grade': grades, 'Student': student})
        return HttpResponse(t.render(c))
        
def sign_in(request, next_page=''):
    """
    Verifies the user. If they are registered, then they are emailed a token to view their grades.
    """
    my_logger.debug('Sign-in')
    if request.method == 'POST':
        form_student_number = request.POST.get('student_number', '')
        my_logger.debug('POST-studentnum: ' + form_student_number)

        try:
            the_student = Student.objects.get(student_number=form_student_number)
        except Student.DoesNotExist:
            # If student number not in list, tell them they are not registered
            return HttpResponseRedirect('/grades/not-registered')
        else:
            token_address = generate_random_token(website_base)
            Token.objects.get_or_create(token_address=token_address, student=the_student, has_been_used=False)
            result = email_token_to_student(the_student.email_address, token_address)
            if result:
                return HttpResponseRedirect('/grades/sent-email')
            else:
                return HttpResponseRedirect('/grades/error')
    
    # Non-POST access of the sign-in page: display the login page to the user
    else:
        my_logger.debug('Non-POST sign-in')
        page_content = {}
        page_content.update(csrf(request) 
        return render_to_response('sign_in_form.html', page_content)

