from django.contrib import admin

from .models import Meeting, ProblemStatement

admin.site.register(ProblemStatement)
admin.site.register(Meeting)
