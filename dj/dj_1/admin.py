from django.contrib import admin
from .models import Historical, Company, Insider, InsiderTrades

admin.site.register(Historical)
admin.site.register(Company)
admin.site.register(Insider)
admin.site.register(InsiderTrades)


