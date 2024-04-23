from django.contrib import admin
from .models import State, District

class StateAdmin(admin.ModelAdmin):
    list_display = ('name',)

class DistrictAdmin(admin.ModelAdmin):
    list_display = ('name', 'state')

admin.site.register(State, StateAdmin)
admin.site.register(District, DistrictAdmin)
