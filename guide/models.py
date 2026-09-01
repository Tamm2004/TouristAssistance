from django.db import models
from django_ckeditor_5.fields import CKEditor5Field
from django.contrib.auth.models import User

class Place(models.Model):
    title = models.CharField(max_length=200,blank=False,null=False)
    image=models.ImageField(blank=False,null=False)
    introduction = CKEditor5Field('Introduction', config_name='default', blank=True, null=True)
    history = CKEditor5Field('History', config_name='default', blank=True, null=True)
    extra = CKEditor5Field('Extra', config_name='default', blank=True, null=True)


    categories = models.ManyToManyField("Category", related_name="places")

    def __str__(self):
        return self.title

class PlaceImage(models.Model):
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name="gallery")
    image = models.ImageField()

    def __str__(self):
        return f"{self.place.title} Image"

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Shop(models.Model):
    owner = models.ForeignKey("Userregister", on_delete=models.CASCADE, related_name="shops", null=True, blank=True)
    title = models.CharField(max_length=200)
    image = models.ImageField()
    address = models.TextField()
    description = CKEditor5Field('Description', config_name='default', blank=True, null=True)
    foods = models.ManyToManyField("Food", related_name="shops", blank=True)
    products = models.ManyToManyField("Product", related_name="shops", blank=True)
    categories = models.ManyToManyField("Category", related_name="shop")



    def __str__(self):
        return self.title

    class Meta:
        unique_together = ('owner', 'title')

class ShopImage(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="gallery")
    image = models.ImageField()

    def __str__(self):
        return f"{self.shop.title} Image"


class Restaurant(models.Model):
    owner = models.ForeignKey("Userregister", on_delete=models.CASCADE, related_name="restaurant", null=True, blank=True)
    title = models.CharField(max_length=200)
    image = models.ImageField()
    address = models.TextField()
    description = CKEditor5Field('Description', config_name='default', blank=True, null=True)
    foods = models.ManyToManyField("Food", related_name="restaurants", blank=True)
    categories = models.ManyToManyField("Category", related_name="restaurant")
    def __str__(self):
        return self.title

    class Meta:
        unique_together = ('owner', 'title')

class RestaurantImage(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="gallery")
    image = models.ImageField()

    def __str__(self):
        return f"{self.restaurant.title} Image"


class RestaurantBranch(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="branches"
    )

    branch_name = models.CharField(max_length=200, blank=True, null=True)

    address = models.TextField()

    image = models.ImageField(upload_to="restaurant_branches/")

    def __str__(self):
        return f"{self.restaurant.title} - {self.branch_name}"

class RestaurantBranchImage(models.Model):
    branch = models.ForeignKey(
        RestaurantBranch,
        on_delete=models.CASCADE,
        related_name="gallery"
    )

    image = models.ImageField(upload_to="restaurant_branch_gallery/")

    def __str__(self):
        return f"{self.branch.restaurant.title} Branch Image"
    
class Food(models.Model):
    owners = models.ManyToManyField("Userregister", related_name="foods", blank=True)
    title = models.CharField(max_length=200)
    image=models.ImageField()
    description = CKEditor5Field('Description', config_name='default', blank=True, null=True)
    categories = models.ManyToManyField("Category", related_name="food")

    def __str__(self):
        return self.title

class Product(models.Model):
    owners = models.ManyToManyField("Userregister", related_name="products", blank=True)
    title = models.CharField(max_length=200)
    image=models.ImageField()
    description = CKEditor5Field('Description', config_name='default', blank=True, null=True)
    categories = models.ManyToManyField("Category", related_name="product")

    def __str__(self):
        return self.title

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="gallery")
    image = models.ImageField()

    def __str__(self):
        return f"{self.product.title} Image"

class Hotel(models.Model):
    owner = models.ForeignKey("Userregister", on_delete=models.CASCADE, related_name="hotels", null=True, blank=True)
    description = CKEditor5Field('Description', config_name='default', blank=True, null=True)
    title = models.CharField(max_length=200)
    image=models.ImageField()
    address = models.TextField(blank=True, null= True)
    categories = models.ManyToManyField("Category", related_name="hotel")



    def __str__(self):
        return self.title

class HotelImage(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="gallery")
    image = models.ImageField()


    def __str__(self):
        return f"{self.hotel.title} Image"

class HotelBranch(models.Model):
    hotel = models.ForeignKey(
        Hotel,
        on_delete=models.CASCADE,
        related_name="branches"
    )

    branch_name = models.CharField(max_length=200, blank=True, null=True)

    address = models.TextField()

    image = models.ImageField(upload_to="hotel_branches/")

    def __str__(self):
        return f"{self.hotel.title} - {self.branch_name}"

class HotelBranchImage(models.Model):
    branch = models.ForeignKey(
        HotelBranch,
        on_delete=models.CASCADE,
        related_name="gallery"
    )

    image = models.ImageField(upload_to="hotel_branch_gallery/")

    def __str__(self):
        return f"{self.branch.hotel.title} Branch Image"

class Userregister(models.Model):
    USER_TYPES = (('Tourist', 'Tourist'),('Business Owner', 'Business Owner'),)
    firstname=models.CharField(max_length=200)
    lastname=models.CharField(max_length=200, null=True, blank=True)
    email=models.EmailField()
    password=models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=USER_TYPES, default='Tourist')

    contact = models.CharField(max_length=15, null=True, blank=True)
    alternate_contact = models.CharField(max_length=15, null=True, blank=True)
    birthday = models.DateField(null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    social_link = models.URLField(null=True, blank=True)
    gender = models.CharField(max_length=10, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    photo = models.ImageField(upload_to='profile_photos/', null=True, blank=True)
    newsletter = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.email}"


class Contact(models.Model):
    name=models.CharField(max_length=200)
    email=models.EmailField()
    message=models.TextField()

class Review(models.Model):
    user = models.ForeignKey(Userregister, on_delete=models.CASCADE, null=True, blank=True)
    place = models.ForeignKey('Place', on_delete=models.CASCADE, null=True, blank=True)
    food = models.ForeignKey('Food', on_delete=models.CASCADE, null=True, blank=True)
    hotel = models.ForeignKey('Hotel', on_delete=models.CASCADE, null=True, blank=True)
    shop = models.ForeignKey('Shop', on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey('Product', on_delete=models.CASCADE, null=True, blank=True)
    restaurant = models.ForeignKey('Restaurant', on_delete=models.CASCADE, null=True, blank=True)
    email = models.EmailField()
    review = models.TextField()
    rating = models.IntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.place:
            return f"{self.email} - Place Review ({self.place.title}) - {self.rating}⭐"
        elif self.food:
            return f"{self.email} - Food Review ({self.food.title}) - {self.rating}⭐"
        elif self.hotel:
            return f"{self.email} - Hotel Review ({self.hotel.title}) - {self.rating}⭐"
        elif self.shop:
            return f"{self.email} - Hotel Review ({self.shop.title}) - {self.rating}⭐"
        elif self.product:
            return f"{self.email} - Product Review ({self.product.title}) - {self.rating}⭐"
        elif self.restaurant:
            return f"{self.email} - Restaurant Review ({self.restaurant.title}) - {self.rating}⭐"
        else:
            return f"{self.email} - Site Review - {self.rating}⭐"

class Wishlist(models.Model):
    user = models.ForeignKey(Userregister, on_delete=models.CASCADE)
    place = models.ForeignKey('Place', on_delete=models.CASCADE, null=True, blank=True)
    food = models.ForeignKey('Food', on_delete=models.CASCADE, null=True, blank=True)
    hotel = models.ForeignKey('Hotel', on_delete=models.CASCADE, null=True, blank=True)
    shop = models.ForeignKey('Shop', on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey('Product', on_delete=models.CASCADE, null=True, blank=True)
    restaurant = models.ForeignKey('Restaurant', on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        if self.place:
            return f"{self.user.email} - {self.place.title}"
        elif self.food:
            return f"{self.user.email} - {self.food.title}"
        elif self.hotel:
            return f"{self.user.email} - {self.hotel.title}"
        elif self.shop:
            return f"{self.user.email} - {self.shop.title}"
        elif self.product:
            return f"{self.user.email} - {self.product.title}"
        elif self.restaurant:
            return f"{self.user.email} - {self.restaurant.title}"
        return self.user.email


class FAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()

    def __str__(self):
        return self.question

class NewsletterSubscriber(models.Model):
    user = models.ForeignKey(Userregister, on_delete=models.CASCADE)
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email

class Recommendation(models.Model):
    TYPE_CHOICES = (
        ('place', 'Place'),
        ('food', 'Food'),
        ('hotel', 'Hotel'),
        ('shop', 'Shop'),
        ('product', 'Product'),
        ('restaurant', 'Restaurant'),
    )

    user = models.ForeignKey(Userregister, on_delete=models.CASCADE, null=True, blank=True)
    item_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    item_id = models.IntegerField()
    title = models.CharField(max_length=255)
    avg_rating = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class WeatherData(models.Model):
    city = models.CharField(max_length=100)
    temperature = models.FloatField()
    feels_like = models.FloatField()
    humidity = models.IntegerField()
    wind_speed = models.FloatField()
    description = models.CharField(max_length=100)
    icon_class = models.CharField(max_length=50)
    background = models.CharField(max_length=100)

    sunrise = models.TimeField()
    sunset = models.TimeField()

    current_date = models.CharField(max_length=50)
    current_time = models.CharField(max_length=50)

    updated_at = models.DateTimeField(auto_now=True)



class CabBooking(models.Model):
    user = models.ForeignKey(Userregister, on_delete=models.CASCADE)

    source = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)
    distance = models.FloatField()

    otp = models.CharField(max_length=6, blank=True, null=True)  # optional for now

    amount = models.IntegerField()
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)

    status = models.CharField(max_length=50, default='Created') 

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.status}"