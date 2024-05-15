from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import ExtendedUser, Material, MaterialVariation, Order, SubOrder, WorkshopInformation


# Extended User
class ExtendedUserAdmin(UserAdmin):
    model = ExtendedUser
    fieldsets = (*UserAdmin.fieldsets, ("Extended Info", {"fields": ("tu_id", "matr_nr")}))


admin.site.register(ExtendedUser, ExtendedUserAdmin)


# Order and Suborder
class SubOrderInline(admin.TabularInline[SubOrder]):
    model = SubOrder
    extra = 0


# @admin.register(Order).
# class OrderAdmin(admin.ModelAdmin):
#     inlines = [
#         SubOrderInline,
#     ]

# class OrderAdmin(admin.ModelAdmin[Order]):
#     inlines = [SubOrderInline]
# admin.site.register(Order, OrderAdmin)


class OrderAdmin(admin.ModelAdmin):
    list_display = ("user", "date_ordered", "state")


admin.site.register(Order, OrderAdmin)


# Material and MaterialVariation
class MaterialVariationInline(admin.TabularInline):
    model = MaterialVariation


@admin.register(Material)
class ClothesAdmin(admin.ModelAdmin):
    inlines = [
        MaterialVariationInline,
    ]


# class MyNestedInline(admin.NestedTabularInline):
#     model = MaterialDim

# class MyInline(admin.NestedStackedInline):
#     model = MaterialVariation
#     inlines = [MyNestedInline,]

# admin.site.register(Order, OrderAdmin)


# WorkshopInformation
admin.site.register(WorkshopInformation)
