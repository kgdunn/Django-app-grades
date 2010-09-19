from django.db import models

class Student(models.Model):
	first_name = models.CharField(max_length=250)
        last_name = models.CharField(max_length=250)
        student_number = models.CharField(max_length=7, unique=True, primary_key=True)
	email_address = models.EmailField()
        manual_grade = models.FloatField(blank=True, null=True)
	has_password = models.BooleanField()
	grad_student = models.BooleanField()
        special_case = models.BooleanField()

	def __unicode__(self):
		return u'%s %s, %s, %s, 400=%s, grade=%s' % (self.first_name, self.last_name, self.email_address, str(self.has_password), str(not self.grad_student), str(self.manual_grade))

class Category(models.Model):
	name = models.CharField(max_length=250)
	fraction = models.FloatField()

	def __unicode__(self):
		return u'%s [%s]' % (self.name, str(int(self.fraction*100)))
	

class WorkUnit(models.Model):
	name = models.CharField(max_length=250)
	max_grade_400 = models.FloatField()
	max_grade_600 = models.FloatField()
	category = models.ForeignKey(Category)

	def __unicode__(self):
		return u'%s, [%s/%s]' % (self.name, str(self.max_grade_400), str(self.max_grade_600))

class Question(models.Model):
	name = models.CharField(max_length=250)
	max_grade_400 = models.FloatField()
	max_grade_600 = models.FloatField()
	workunit = models.ForeignKey(WorkUnit)

	def __unicode__(self):
		return u'%s [%s]' % (self.name, str(self.max_grade_400))

class Grade(models.Model):
	grade = models.FloatField(blank=True, null=True)
	grade_char = models.CharField(max_length=1, blank=True, null=True)
	question = models.ForeignKey(Question)
	student = models.ForeignKey(Student)

class GradeSummary(models.Model):
    # If levels==0, then the summary is a histogram; 
    # If levels!=0, then the level_counts field contains the levels counts for each level
    # level_names = ['alpha', 'beta', 'gamma'] etc
    question = models.ForeignKey(Question)
    levels = models.IntegerField()
    level_counts = models.CommaSeparatedIntegerField(blank=True, null=True, max_length=500)
    level_names = models.CharField(max_length=1000, blank=True, null=True)
    summary_str = models.CharField(max_length=1000, blank=True, null=True)
    url_string = models.CharField(max_length=255)
    
    def __unicode__(self):
        return u'%s, [%s] [%s]' % (self.question.name, self.summary_str, self.level_counts)


class WorkUnitSummary(models.Model):
    """ Summary for a work unit (e.g. Assignment 2) """
    workunit = models.ForeignKey(WorkUnit)
    summary_str = models.CharField(max_length=1000, blank=True, null=True)
    url_string = models.CharField(max_length=255)
    
    def __unicode__(self):
        return u'%s, [%s]' % (self.workunit.name, self.summary_str)

class CategorySummary(models.Model):
    """ Summary for a category (e.g. Assignments) """
    category = models.ForeignKey(Category)
    summary_str = models.CharField(max_length=1000, blank=True, null=True)
    url_string = models.CharField(max_length=255)
    def __unicode__(self):
        return u'%s, [%s]' % (self.category.name, self.summary_str)

class Token(models.Model):
    student = models.ForeignKey(Student)
    token_address = models.CharField(max_length=250)
    has_been_used = models.BooleanField(default=False)
    
    def __unicode__(self):
        return u'%s, %s, %s' % (str(self.has_been_used), str(self.student), self.token_address)


