from django.contrib import admin
from grades.student.models import Student, WorkUnit, Question, Grade, Category, GradeSummary, CategorySummary, WorkUnitSummary, Token

class TokenAdmin(admin.ModelAdmin):
    list_per_page = 2000
    list_display = ('student', 'token_address', 'has_been_used', )

admin.site.register(Student)
admin.site.register(WorkUnit)
admin.site.register(Question)
admin.site.register(Grade)
admin.site.register(Category)
admin.site.register(GradeSummary)
admin.site.register(CategorySummary)
admin.site.register(WorkUnitSummary)
admin.site.register(Token, TokenAdmin)
