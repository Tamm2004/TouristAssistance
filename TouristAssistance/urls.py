"""
URL configuration for TouristAssistance project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from guide import views

from django.conf import settings
from django.contrib.staticfiles.urls import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns


urlpatterns = [
    path("admin/", admin.site.urls),
    path("base/", views.base,name="base"),
    path("sidebar/", views.sidebar,name="sidebar"),
    path('', views.index, name="index"),
    path("itinerary/", views.itinerary,name="itinerary"),
    path("login/", views.login,name="login"),
    path("logout/", views.logout,name="logout"),
    path("forgot/", views.forgot,name="forgot"),
    path("reset_pass/", views.reset_pass,name="reset_pass"),
    path("register/", views.register,name="register"),
    path("otp/", views.otp,name="otp"),
    path("review/", views.review,name="review"),
    path("contact_us/", views.contact_us,name="contact_us"),
    path("about_us/", views.about_us,name="about_us"),
    path("places_to_visit/", views.places_to_visit,name="places_to_visit"),
    path("food_to_eat/", views.food_to_eat,name="food_to_eat"),
    path("hotels_to_stay/", views.hotels_to_stay,name="hotels_to_stay"),
    path("restaurants_to_explore/", views.restaurants_to_explore,name="restaurants_to_explore"),
    path("wishlist/", views.wishlist,name="wishlist"),
    path('toggle-wishlist/', views.toggle_wishlist, name="toggle_wishlist"),
    path('remove-wishlist/<int:id>/', views.remove_wishlist, name="remove_wishlist"),
    path("ckeditor5/", include('django_ckeditor_5.urls')),
    path("place/<int:id>", views.place,name="place"),
    path("food/<int:id>", views.food,name="food"),
    path("hotel/<int:id>", views.hotel,name="hotel"),
    path("restaurant/<int:id>", views.restaurant,name="restaurant"),
    path("products_to_buy/", views.products_to_buy,name="products_to_buy"),
    path("product/<int:id>", views.product,name="product"),
    path("all_shops/", views.all_shops,name="all_shops"),
    path("shop/<int:id>", views.shop,name="shop"),
    path("dashboard/", views.dashboard,name="dashboard"),
    path("add_business/", views.add_business,name="add_business"),
    path('business_listing/', views.business_listing, name='business_listing'),
    path('delete/<str:type>/<int:id>/', views.delete_business, name='delete_business'),
    path("search/", views.search, name="search"),
    path('subscribe/', views.subscribe_newsletter, name='subscribe_newsletter'),
    path('chatbot/', views.chatbot, name='chatbot'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('chatbot/get-response/', views.chatbot_response, name='chatbot_response'),
    path("transportation/", views.transportation, name="transportation"),
    path('paymenthandler/', views.paymenthandler, name='paymenthandler'),

]

urlpatterns+=staticfiles_urlpatterns()
urlpatterns+=static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
