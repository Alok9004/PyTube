from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin


admin.site.unregister(User)

class accountsAdmin(UserAdmin):
    list_display = ('username', 'email')
    search_fields = ('username', 'email')


admin.site.register(User,accountsAdmin)