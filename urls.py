from django.conf.urls.defaults import *
from grades.student import views

urlpatterns = patterns('grades.student',
    (r'^$', views.sign_in),			
    (r'^/$', views.sign_in),
    (r'^not-registered', views.not_registered_sign_in),
    (r'^sent-email', views.sent_email_sign_in),
    (r'^error', views.generic_error),
    (r'^tokens/(.*)/$', views.process_token),
)

