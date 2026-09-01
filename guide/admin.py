from django.contrib import admin
from guide.models import Userregister
from guide.models import Place
from guide.models import Category
from guide.models import Food
from guide.models import (Hotel, HotelBranch, HotelImage, HotelBranchImage)
from guide.models import Shop
from guide.models import Review
from guide.models import Contact
from guide.models import Product
from guide.models import ProductImage
from guide.models import PlaceImage
from guide.models import ShopImage
from guide.models import (Restaurant, RestaurantBranch, RestaurantImage, RestaurantBranchImage)
from guide.models import Wishlist
from guide.models import FAQ
from guide.models import NewsletterSubscriber
from guide.models import Recommendation
from guide.models import WeatherData
from guide.models import CabBooking

VENDOR_CATEGORY = "Business Owner"


class VendorOwnerAdminMixin:
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "owner":
            kwargs["queryset"] = Userregister.objects.filter(category=VENDOR_CATEGORY)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class VendorOwnersAdminMixin:
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "owners":
            kwargs["queryset"] = Userregister.objects.filter(category=VENDOR_CATEGORY)
        return super().formfield_for_manytomany(db_field, request, **kwargs)


class PlaceImageInline(admin.TabularInline):
    model = PlaceImage
    extra = 1

class PlaceAdmin(admin.ModelAdmin):
    filter_horizontal = ('categories',)
    inlines = [PlaceImageInline]


class ShopImageInline(admin.TabularInline):
    model = ShopImage
    extra = 1

class ShopAdmin(VendorOwnerAdminMixin, admin.ModelAdmin):
	filter_horizontal = ('foods', 'products','categories')
	inlines = [ShopImageInline]

class RestaurantImageInline(admin.TabularInline):
    model = RestaurantImage
    extra = 1

class RestaurantAdmin(VendorOwnerAdminMixin, admin.ModelAdmin):
    filter_horizontal = ('foods','categories')
    inlines = [RestaurantImageInline]
    list_display = ('title', 'owner')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change and obj.image and not obj.branches.exists():
            RestaurantBranch.objects.create(
                restaurant=obj,
                branch_name="Main Branch",
                address=obj.address,
                image=obj.image,
            )

class RestaurantBranchImageInline(admin.TabularInline):
    model = RestaurantBranchImage
    extra = 1

class RestaurantBranchAdmin(admin.ModelAdmin):
    inlines = [RestaurantBranchImageInline]
    list_display = ('restaurant', 'branch_name', 'address')



class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class ProductAdmin(VendorOwnersAdminMixin, admin.ModelAdmin):
    filter_horizontal = ('owners', 'categories') 
    inlines = [ProductImageInline]

class HotelImageInline(admin.TabularInline):
    model = HotelImage
    extra = 1



class HotelAdmin(VendorOwnerAdminMixin, admin.ModelAdmin):
    filter_horizontal = ('categories',) 
    inlines = [HotelImageInline]
    list_display = ('title', 'owner')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change and obj.image and not obj.branches.exists():
            HotelBranch.objects.create(
                hotel=obj,
                branch_name="Main Branch",
                address="",
                image=obj.image,
            )

class HotelBranchImageInline(admin.TabularInline):
    model = HotelBranchImage
    extra = 1

class HotelBranchAdmin(admin.ModelAdmin):
    inlines = [HotelBranchImageInline]

    list_display = ('hotel', 'branch_name', 'address')


class FoodAdmin(VendorOwnersAdminMixin, admin.ModelAdmin):
    filter_horizontal = ('owners','categories')

admin.site.register(Place, PlaceAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Category)
admin.site.register(Userregister)
admin.site.register(Food, FoodAdmin)
admin.site.register(Hotel, HotelAdmin)
admin.site.register(Shop, ShopAdmin)
admin.site.register(Restaurant, RestaurantAdmin)
admin.site.register(Review)
admin.site.register(Contact)
admin.site.register(Wishlist)
admin.site.register(FAQ)
admin.site.register(NewsletterSubscriber)
admin.site.register(Recommendation)
admin.site.register(WeatherData)
admin.site.register(CabBooking)
admin.site.register(RestaurantBranch, RestaurantBranchAdmin)
admin.site.register(HotelBranch, HotelBranchAdmin)










