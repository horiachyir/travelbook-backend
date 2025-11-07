from django.contrib import admin
from .models import Destination, SystemSettings, Vehicle, FinancialConfig, PaymentFee, PaymentAccount, TermsConfig

# Register your models here.
admin.site.register(Destination)
admin.site.register(SystemSettings)
admin.site.register(Vehicle)
admin.site.register(FinancialConfig)
admin.site.register(PaymentFee)
admin.site.register(PaymentAccount)
admin.site.register(TermsConfig)
