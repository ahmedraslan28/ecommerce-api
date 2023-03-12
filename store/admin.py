from django.contrib import admin
from . import models
from django.contrib.auth.hashers import make_password
# Register your models here.


class UserAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        obj.password = make_password(obj.password)
        obj.save()


admin.site.register(models.User, UserAdmin)
admin.site.register(models.ProductImage)
admin.site.register(models.Product)
admin.site.register(models.Order)
admin.site.register(models.Customer)
admin.site.register(models.Collection)
admin.site.register(models.Review)
admin.site.register(models.Cart)
admin.site.register(models.CartItem)
