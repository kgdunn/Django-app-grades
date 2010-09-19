from django.contrib import admin
from grades.student.models import Student, WorkUnit, Question, Grade, Category, GradeSummary, CategorySummary, WorkUnitSummary, Token

admin.site.register(Student)
admin.site.register(WorkUnit)
admin.site.register(Question)
admin.site.register(Grade)
admin.site.register(Category)
admin.site.register(GradeSummary)
admin.site.register(CategorySummary)
admin.site.register(WorkUnitSummary)
admin.site.register(Token)
