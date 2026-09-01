from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.db.models import Avg ,Count
from django.core.mail import send_mail
from guide.models import Userregister
from django.http import JsonResponse
from guide.models import Wishlist
from django.conf import settings
from guide.models import Contact
from guide.models import Review
from guide.models import Place
from guide.models import Food
from guide.models import Hotel
from guide.models import HotelBranch
from guide.models import Shop
from guide.models import Product
from guide.models import Restaurant
from guide.models import RestaurantBranch
from guide.models import RestaurantImage
from guide.models import RestaurantBranchImage
from guide.models import ShopImage
from guide.models import PlaceImage
from guide.models import ProductImage
from guide.models import HotelImage
from guide.models import HotelBranchImage
from guide.models import FAQ
from guide.models import Recommendation
from guide.models import NewsletterSubscriber
from guide.models import WeatherData
from guide.models import CabBooking
from django.contrib import messages
from datetime import datetime
from django.db.models import Q
from django.db.models import Prefetch
from .utils import get_bot_response
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseBadRequest
import requests
import random
import pytz
import re
import razorpay
import json



def chatbot(request):
    return render(request, 'chatbot.html')

def chatbot_response(request):
    user_message = request.GET.get('message')
    response = get_bot_response(user_message, request)
    return JsonResponse(response)



client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

def transportation(request):
    if not request.session.get('email'):
        return redirect('login')

    user = Userregister.objects.get(email=request.session['email'])

    message = request.session.pop('payment_status', None)
    context = {}
    if message:
        context['message'] = message
    if request.method == "POST":
        from_l= request.POST.get("from_location")
        to_l = request.POST.get("to_location")
        from_loc = request.POST.get("from_location")+ ",Amritsar, Punjab, India"
        to_loc = request.POST.get("to_location")+ ",Amritsar, Punjab, India"
        lat1, lon1 = get_coordinates(from_loc)
        lat2, lon2 = get_coordinates(to_loc)
        if lat1 is not None and lat2 is not None:
            print("FROM:", lat1, lon1)
            print("TO:", lat2, lon2)
            distance = get_distance(lat1, lon1, lat2, lon2)
            if distance is None:
                return render(request,'transportation.html',{"error":"Unable to calculate distance"})
            else:
                suggestion = suggest_transport(distance)
                if suggestion == "Cab":
                    fare = round(calculate_fare(distance), 2)
                    amount = int(fare * 100)
                    currency = 'INR'
                    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


                    razorpay_order = client.order.create(
                        dict(amount=amount, currency=currency, payment_capture='0')
                    )
                    
                    CabBooking.objects.create(
                        user=user,
                        source=from_loc,
                        destination=to_loc,
                        distance=distance,
                        amount=amount,
                        razorpay_order_id=razorpay_order['id'],
                        status='Created'
                        )
                    context = {
                        'razorpay_order_id': razorpay_order['id'],
                        'razorpay_merchant_key': settings.RAZORPAY_KEY_ID,
                        'razorpay_amount': amount,
                        'currency': currency,
                        'distance':distance,
                        'suggestion':suggestion,
                        'amount':fare,
                        'from_l':from_l,
                        'to_l':to_l
                    }
                    return render(request, 'transportation.html', context)
                else:
                    currency = 'INR'
                    context = {
                        'currency': currency,
                        'distance':distance,
                        'suggestion':suggestion,
                        'from_l':from_l,
                        'to_l':to_l
                    }
                    return render(request, 'transportation.html', context)
        else:
            return render(request,'transportation.html',{"error":"No latitude and longitude"})

    return render(request, 'transportation.html')

@csrf_exempt
def paymenthandler(request):
    if request.method == "POST":
        payment_id = request.POST.get('razorpay_payment_id', '')
        razorpay_order_id = request.POST.get('razorpay_order_id', '')
        signature = request.POST.get('razorpay_signature', '')
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }

        try:
            client.utility.verify_payment_signature(params_dict)
            


            booking = CabBooking.objects.get(razorpay_order_id=razorpay_order_id)
            user = booking.user
            email = user.email

            capture_amount = int(booking.amount)
            

            client.payment.capture(payment_id, capture_amount)
            
            otp = str(random.randint(100000, 999999))
            booking.razorpay_payment_id = payment_id
            booking.razorpay_signature = signature
            booking.status='Success'
            booking.otp=otp
            booking.razorpay_payment_id = payment_id
            booking.save()
            email=booking.user.email
            request.session['payment_status'] = "Success"
            user=Userregister.objects.get(email=email)
            request.session['id'] = user.id
            request.session['email']=user.email
            request.session['is_logged_in'] = True
            request.session['category'] = user.category 

            send_mail(subject="Cab Booking Confirmed 🚕",
                message=f"""Hello, Your cab booking is confirmed!
                From: {booking.source}
                To: {booking.destination}
                Distance: {booking.distance:.2f} km
                🔐 OTP: {booking.otp}
                Share this OTP with your driver to start the ride.
                Thank you!""",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False,)
            return redirect('transportation')

        except razorpay.errors.SignatureVerificationError:
            CabBooking.objects.filter(razorpay_order_id=razorpay_order_id).update(status='Failed')
            request.session['payment_status'] = "Failed"
            return redirect('transportation')
            
        except Exception as e:
            
            return HttpResponseBadRequest(f"Payment Processing Error: {str(e)}")
    else:
        return HttpResponseBadRequest("Invalid request method")

def get_coordinates(location):
    url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": location,
        "format": "json",
        "limit":1
    }

    headers = {
        "User-Agent": "TamannaTransportApp/1.0" 
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)

        if response.status_code != 200:
            return None, None

        data = response.json()

        if data:
            return float(data[0]['lat']), float(data[0]['lon'])

    except requests.exceptions.RequestException:
        return None, None

    return None, None

def get_distance(lat1, lon1, lat2, lon2):
    url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false"

    try:
        response = requests.get(url, timeout=5)

        if response.status_code != 200:
            return None

        data = response.json()

        if 'routes' in data and len(data['routes']) > 0:
            return data['routes'][0]['distance'] / 1000

    except requests.exceptions.RequestException:
        return None

    return None

def suggest_transport(distance):
    if distance < 1:
        return "Walking"
    elif distance < 5:
        return "Auto Rickshaw"
    else:
        return "Cab"

def calculate_fare(distance):
    base_fare = 50
    per_km = 12
    return base_fare + (distance * per_km)



def get_recommendations(user):
    wishlist = Wishlist.objects.filter(user=user) if user else Wishlist.objects.none()

    wishlist_places = wishlist.filter(place__isnull=False).values_list('place_id', flat=True)
    wishlist_foods = wishlist.filter(food__isnull=False).values_list('food_id', flat=True)
    wishlist_hotels = wishlist.filter(hotel__isnull=False).values_list('hotel_id', flat=True)
    wishlist_products = wishlist.filter(product__isnull=False).values_list('product_id', flat=True)
    wishlist_shops = wishlist.filter(shop__isnull=False).values_list('shop_id', flat=True)
    wishlist_restaurants = wishlist.filter(restaurant__isnull=False).values_list('restaurant_id', flat=True)



    recommended_places_wishlist = Place.objects.none()
    if wishlist_places:
        categories = Place.objects.filter(id__in=wishlist_places).values_list('categories', flat=True)

        recommended_places_wishlist = Place.objects.filter(categories__in=categories)\
            .exclude(id__in=wishlist_places)\
            .distinct().annotate(avg_rating=Avg('review__rating')).order_by('-avg_rating')[:3]

    recommended_foods_wishlist = Food.objects.exclude(id__in=wishlist_foods)\
        .annotate(avg_rating=Avg('review__rating')).order_by('-avg_rating')[:2]

    recommended_hotels_wishlist = Hotel.objects.exclude(id__in=wishlist_hotels)\
        .annotate(avg_rating=Avg('review__rating')).order_by('-avg_rating')[:2]

    recommended_products_wishlist = Product.objects.exclude(id__in=wishlist_products)\
        .annotate(avg_rating=Avg('review__rating')).order_by('-avg_rating')[:2]

    recommended_shops_wishlist = Shop.objects.exclude(id__in=wishlist_shops)\
        .annotate(avg_rating=Avg('review__rating')).order_by('-avg_rating')[:2]

    recommended_restaurants_wishlist = Restaurant.objects.exclude(id__in=wishlist_restaurants)\
        .annotate(avg_rating=Avg('review__rating')).order_by('-avg_rating')[:2]


    top_places = Place.objects.annotate(avg_rating=Avg('review__rating')).order_by('-avg_rating')[:2]
    top_foods = Food.objects.annotate(avg_rating=Avg('review__rating')).order_by('-avg_rating')[:1]
    top_hotels = Hotel.objects.annotate(avg_rating=Avg('review__rating')).order_by('-avg_rating')[:1]
    top_products = Product.objects.annotate(avg_rating=Avg('review__rating')).order_by('-avg_rating')[:1]
    top_shops = Shop.objects.annotate(avg_rating=Avg('review__rating')).order_by('-avg_rating')[:1]
    top_restaurants = Restaurant.objects.annotate(avg_rating=Avg('review__rating')).order_by('-avg_rating')[:1]




    random_places = Place.objects.order_by('?')[:1]
    random_foods = Food.objects.order_by('?')[:1]
    random_hotels = Hotel.objects.order_by('?')[:1]
    random_products = Product.objects.order_by('?')[:1]
    random_shops = Shop.objects.order_by('?')[:1]
    random_restaurants = Restaurant.objects.order_by('?')[:1]



    recommended_items = []

    recommended_items += list(recommended_places_wishlist)
    recommended_items += list(recommended_foods_wishlist)
    recommended_items += list(recommended_hotels_wishlist)
    recommended_items += list(recommended_products_wishlist)
    recommended_items += list(recommended_shops_wishlist)
    recommended_items += list(recommended_restaurants_wishlist)



    recommended_items += list(top_places)
    recommended_items += list(top_foods)
    recommended_items += list(top_hotels)
    recommended_items += list(top_products)
    recommended_items += list(top_shops)
    recommended_items += list(top_restaurants)



    recommended_items += list(random_places)
    recommended_items += list(random_foods)
    recommended_items += list(random_hotels)
    recommended_items += list(random_products)
    recommended_items += list(random_shops)
    recommended_items += list(random_restaurants)


    unique_items = []
    seen_ids = set()

    for item in recommended_items:
        unique_id = f"{item.__class__.__name__}_{item.id}"
        if unique_id not in seen_ids:
            seen_ids.add(unique_id)
            unique_items.append(item)

    random.shuffle(unique_items)
    final_items = unique_items[:8]


    final_data = []
    Recommendation.objects.filter(user=user).delete()

    for item in final_items:
        if isinstance(item, Place):
            item_type = "place"
            title = item.title
        elif isinstance(item, Food):
            item_type = "food"
            title = item.title
        elif isinstance(item, Hotel):
            item_type = "hotel"
            title = item.title
        elif isinstance(item, Product):
            item_type = "product"
            title = item.title
        elif isinstance(item, Restaurant):
            item_type = "restaurant"
            title = item.title
        else:
            item_type = "hotel"
            title = item.title

        Recommendation.objects.create(
            user=user,
            item_type=item_type,
            item_id=item.id,
            title=title,
            avg_rating=getattr(item, 'avg_rating', None))

        final_data.append({
            "type": item_type,
            "data": item
        })

    return final_data


def base(request):
    try:
        email = request.session.get('email')
        user = Userregister.objects.get(email=email)
    except:
        user=None
    return render(request,'base.html',{"user":user})

def sidebar(request):
    email=request.session.get('email')
    user=Userregister.objects.get(email=email)
    return render(request,'sidebar.html',{"user":user})

def itinerary(request):
    return render(request,'itinerary.html')

def login(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            user = Userregister.objects.get(email=email)
        except Userregister.DoesNotExist:
            return render(request, 'login.html', {'ms': 'Invalid email'})

        if check_password(password, user.password):
            request.session['user_id'] = user.id
            request.session['email'] = user.email
            request.session['is_logged_in'] = True
            request.session['category'] = user.category 
            if user.category == "Business Owner":
                return redirect('dashboard')
            else:
                return redirect('index')
        else:
            return render(request, 'login.html', {'ms': 'Invalid password', 'email':email})
    else:
        return render(request, 'login.html')


def forgot(request):
    if request.method =='POST':
        email = request.POST.get('email')
        try:
            user = Userregister.objects.get(email=email)
        except Userregister.DoesNotExist:
            return render(request, 'forgot.html', {'ms': 'Invalid email'})
        otp_length = 6
        o_otp = ''.join(random.choices('0123456789', k=otp_length))
        subject="OTP Verification"
        message="Welcome to AmritPath! \n Your OTP is "+o_otp
        email_from=settings.EMAIL_HOST_USER
        recipient_list=[email,]
        send_mail(subject,message,email_from,recipient_list)
        return render(request,'otp.html',{'o_otp':o_otp,'email':email})
    else:
        return render(request,'forgot.html')

def register(request):
    if request.method=="POST":
        firstname=request.POST.get('firstname')
        lastname=request.POST.get('lastname')
        email=request.POST.get('email')
        password=request.POST.get('password')
        confirmpassword=request.POST.get('confirmpassword')
        category = request.POST.get('user_type')
        if Userregister.objects.filter(email=email).exists():
            return render(request,'register.html',{'ms':"Already registered"})
        else:
            if password==confirmpassword:
                    otp_length = 6
                    o_otp = ''.join(random.choices('0123456789', k=otp_length))
                    subject="OTP Verification"
                    message="Welcome to AmritPath! \n Your OTP is "+o_otp
                    email_from=settings.EMAIL_HOST_USER
                    recipient_list=[email,]
                    send_mail(subject,message,email_from,recipient_list)
                    password=make_password(password)
                    category=category
                    return render(request,'otp.html',{'o_otp':o_otp,'email':email,'firstname':firstname, 'lastname':lastname, 'password':password, 'category':category})
            else:
                    return render(request,'register.html',{'ms':"Incorrect Pass",'email':email,'firstname':firstname, 'lastname':lastname})
    else:
        return render(request,'register.html')

def otp(request):
    if request.method == 'POST':
        email=request.POST.get('email')
        otp=request.POST.get('otp')
        o_otp=request.POST.get('o_otp')
        if Userregister.objects.filter(email=email).exists():
            if otp==o_otp:
                return render(request,'reset_pass.html',{'email':email})
            else:
                return render(request,'otp.html',{'email':email,'ms':"Incorrect otp", 'o_otp':o_otp})
        else:
            firstname=request.POST.get('firstname')
            lastname=request.POST.get('lastname')
            password=request.POST.get('password')
            category=request.POST.get('category')
            otp=request.POST.get('otp')
            o_otp=request.POST.get('o_otp')
            if otp==o_otp:
                x=Userregister()
                x.firstname=firstname
                x.lastname=lastname
                x.email=email
                x.password=password
                x.category=category
                x.save()
                request.session['user_id'] = x.id
                request.session['email'] = x.email
                request.session['category'] = x.category 
                if x.category == "Business Owner":
                    return redirect('dashboard')
                else:
                    return redirect('index')
            else:
                return render(request,'otp.html',{'ms':"Incorrect otp", 'email':email, 'o_otp':o_otp, 'firstname':firstname, 'lastname':lastname, 'password':password})
    else:
        return render(request,'otp.html')

def reset_pass(request):
    if request.method == 'POST':
        email=request.POST.get('email')
        password=request.POST.get('password')
        confirmpassword=request.POST.get('confirmpassword')
        if password==confirmpassword:
            x=Userregister.objects.get(email=email)
            x.password=make_password(password)
            x.save()
            return redirect('login')
        else:
            return render(request,'reset_pass.html',{'ms': "Incorrect pass",'email':email})
    else:
        return render(request,'reset_pass.html')
def review(request):
    if 'email' not in request.session:
        return redirect('login')
    site_reviews = Review.objects.filter(place__isnull=True,food__isnull=True,hotel__isnull=True,shop__isnull=True, product__isnull=True, restaurant__isnull=True)
    user = Userregister.objects.get(email=request.session['email'])
    if request.method == "POST":
        review_text = request.POST.get('review')
        rating = request.POST.get('rating')
        if not rating:
            return render(request, 'review.html', {'error': 'Please select rating','user':user, 'review_text':review_text,'site_reviews':site_reviews})
        Review.objects.create(
            user=user,
            email=user.email,
            review=review_text,
            rating=int(rating)
        )
        return redirect('review') 
    return render(request,'review.html',{'user':user,'site_reviews':site_reviews})

def contact_us(request):
    try:
        email = request.session.get('email')
        user = Userregister.objects.get(email=email)
    except:
        user=None
    if request.method == 'POST':
        x=Contact() 
        x.name=request.POST.get('name')
        x.email=request.POST.get('email')
        x.message=request.POST.get('message')
        x.save()
        return render(request,'contact_us.html',{'message':"Your Query is submitted","user":user})
    else:
        return render(request,'contact_us.html',{"user":user})

def index(request):
    faqs = FAQ.objects.all()[:7]
    if 'email' not in request.session:
        user=None
    else:
        user = Userregister.objects.get(email=request.session['email'])
    recommended_items = get_recommendations(user)
    wishlist = Wishlist.objects.filter(user=user)
    wishlist_place_ids = wishlist.values_list('place_id', flat=True)
    wishlist_food_ids = wishlist.values_list('food_id', flat=True)
    wishlist_hotel_ids = wishlist.values_list('hotel_id', flat=True)
    wishlist_product_ids = wishlist.values_list('product_id', flat=True)
    wishlist_restaurant_ids = wishlist.values_list('restaurant_id', flat=True)
    site_reviews = Review.objects.filter(place__isnull=True,food__isnull=True,hotel__isnull=True,shop__isnull=True,product__isnull=True,restaurant__isnull=True)
    average_rating = site_reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    average_rating = round(average_rating, 2)
    random_reviews = site_reviews.order_by('?')[:4]
    total_reviews = site_reviews.count()
    rating_counts = {
    5: site_reviews.filter(rating=5).count(),
    4: site_reviews.filter(rating=4).count(),
    3: site_reviews.filter(rating=3).count(),
    2: site_reviews.filter(rating=2).count(),
    1: site_reviews.filter(rating=1).count(),
    }
    reviews = random_reviews
    try:
        city = "Amritsar" 
        api_key = settings.WEATHER_API_KEY
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        response = requests.get(url)
        data = response.json()
        if response.status_code == 200:
            india_timezone = pytz.timezone("Asia/Kolkata")
            current_time = datetime.now(india_timezone)
            formatted_date = current_time.strftime("%d %B %Y")
            formatted_time = current_time.strftime("%I:%M %p")

            sunrise_time = datetime.fromtimestamp(data['sys']['sunrise'], india_timezone)
            sunset_time = datetime.fromtimestamp(data['sys']['sunset'], india_timezone)

            humidity = data['main']['humidity']
            temperature = data['main']['temp']
            wind_speed = data['wind']['speed']
            description = data['weather'][0]['description'].lower()

            is_night = current_time > sunset_time or current_time < sunrise_time
            icon_class = "icofont-fully-sunny"

            if "rain" in description or "drizzle" in description or "thunderstorm" in description:
                if is_night:
                    background = "Rainy_night.jpeg"
                    icon_class = "icofont-rainy-night"

                else:
                    background = "Rainy.avif"
                    icon_class = "icofont-rainy-sunny"


            elif temperature < 15:
                if is_night:
                    background = "Cold_night.jpg"
                    icon_class = "icofont-snowy-night"

                else:
                    background = "Cold.jpg"
                    icon_class = "icofont-snowy-sunny"


            elif wind_speed > 6 or humidity > 80:
                if is_night:
                    background = "Windy_night.jpg"
                    icon_class = "icofont-windy-night"

                else:
                    background = "Windy.jpg"
                    icon_class = "icofont-windy"

            else:
                if is_night:
                    background = "Night.jpg"
                    icon_class = "icofont-full-night"
                else:
                    background = "Sunny2.avif"
                    icon_class = "icofont-full-sunny"

        

            wind_speed = data['wind']['speed']
            wind_degree = data['wind']['deg']

            wind_speed_kmh = round(wind_speed * 3.6, 1)
            wind_direction = get_wind_direction(wind_degree)
        
            result = {
                'city': city,
                'temperature': data['main']['temp'],
                'feels_like': data['main']['feels_like'],
                'min_temp': data['main']['temp_min'],
                'max_temp': data['main']['temp_max'],
                'humidity': humidity,
                'wind_speed': wind_speed_kmh,
                'wind_degree': wind_degree,  
                'wind_direction': wind_direction,
                'description': data['weather'][0]['main'],
                'icon_class': icon_class,
                'sunrise': sunrise_time.strftime("%I:%M %p"),
                'sunset': sunset_time.strftime("%I:%M %p"),
                'background': background,
                'current_date': formatted_date,
                'current_time': formatted_time
            }
            WeatherData.objects.update_or_create(
                city=city,
                defaults={
                'temperature': result['temperature'],
                'feels_like': result['feels_like'],
                'humidity': result['humidity'],
                'wind_speed': result['wind_speed'],
                'description': result['description'],
                'icon_class': result['icon_class'],
                'background': result['background'],
                'sunrise': sunrise_time.time(),
                'sunset': sunset_time.time(),
                'current_date': result['current_date'],
                'current_time': result['current_time']
                })
        else:
            result = {
                'error': "Weather data not available"
            }
    except Exception as e:
        print("Weather API Error:", e)
        result = None

    places = Place.objects.filter(categories__name="Famous").annotate(avg_rating=Avg('review__rating')).order_by('?')[:6]
    foods = Food.objects.annotate(avg_rating=Avg('review__rating')).order_by('?')[:6] 
    hotels = Hotel.objects.annotate(avg_rating=Avg('review__rating')).order_by('?')[:6]
    products = Product.objects.annotate(avg_rating=Avg('review__rating')).order_by('?')[:6]
    restaurants = Restaurant.objects.annotate(avg_rating=Avg('review__rating')).order_by('?')[:6] 
    if 'email' in request.session:
        user = Userregister.objects.get(email=request.session['email'])
        return render(request, 'index.html', {'user': user,'places':places,'foods':foods,'hotels':hotels,'products':products,'restaurants':restaurants,'result':result,
            'average_rating': average_rating,'reviews':reviews,'total_reviews': total_reviews,
            'rating_counts': rating_counts, 'wishlist_place_ids': wishlist_place_ids,
            'wishlist_food_ids': wishlist_food_ids,'wishlist_hotel_ids': wishlist_hotel_ids,'wishlist_product_ids': wishlist_product_ids,'wishlist_restaurant_ids': wishlist_restaurant_ids,'recommended_items': recommended_items, 'faqs':faqs})
    else:
        return render(request,'index.html',{'places':places,'foods':foods,'products':products,'restaurants':restaurants,'hotels':hotels,'result':result,'average_rating':average_rating,
            'reviews':reviews, 'total_reviews': total_reviews,'rating_counts': rating_counts,
            'wishlist_place_ids': wishlist_place_ids,'wishlist_food_ids': wishlist_food_ids,'wishlist_product_ids': wishlist_product_ids,'wishlist_restaurant_ids': wishlist_restaurant_ids,'wishlist_hotel_ids': wishlist_hotel_ids, 'recommended_items': recommended_items, 'faqs':faqs})



def get_wind_direction(degree):
    directions = ['North', 'North-East', 'East', 'South-East', 'South', 'South-West', 'West', 'North-West']
    index = round(degree / 45) % 8
    return directions[index]

def logout(request):
    request.session.flush()
    return redirect('index')

def about_us(request):
    try:
        email = request.session.get('email')
        user = Userregister.objects.get(email=email)
    except:
        user=None
    return render(request,'about_us.html',{"user":user})

def places_to_visit(request):
    if 'email' not in request.session:
        return redirect('login')
    user = Userregister.objects.get(email=request.session['email'])
    wishlist = Wishlist.objects.filter(user=user)
    wishlist_ids = wishlist.values_list('place_id', flat=True)
    res = Place.objects.all()
    famous = Place.objects.filter(categories__name="Famous").annotate(avg_rating=Avg('review__rating'))
    gurudwara = Place.objects.filter(categories__name="Gurudwaras").annotate(avg_rating=Avg('review__rating'))
    hidden = Place.objects.filter(categories__name="Hidden Gems").annotate(avg_rating=Avg('review__rating'))
    others = Place.objects.filter(categories__name="Others").annotate(avg_rating=Avg('review__rating'))
    return render(request,'places_to_visit.html', {'res':res, 'famous':famous, 'gurudwara':gurudwara,
        'hidden':hidden, 'others':others, 'wishlist_ids': wishlist_ids,"user":user})

def food_to_eat(request):
    if 'email' not in request.session:
        return redirect('login')
    user = Userregister.objects.get(email=request.session['email'])
    wishlist = Wishlist.objects.filter(user=user)
    wishlist_ids = wishlist.values_list('food_id', flat=True)
    res = Food.objects.annotate(avg_rating=Avg('review__rating'))
    return render(request,'food_to_eat.html', {'res':res, 'wishlist_ids': wishlist_ids,"user":user})

def hotels_to_stay(request):
    if 'email' not in request.session:
        return redirect('login')
    user = Userregister.objects.get(email=request.session['email'])
    wishlist = Wishlist.objects.filter(user=user)
    wishlist_ids = wishlist.values_list('hotel_id', flat=True)
    res = Hotel.objects.annotate(avg_rating=Avg('review__rating'))
    return render(request,'hotels_to_stay.html', {'res':res, 'wishlist_ids': wishlist_ids,"user":user})

def restaurants_to_explore(request):
    if 'email' not in request.session:
        return redirect('login')
    user = Userregister.objects.get(email=request.session['email'])
    wishlist = Wishlist.objects.filter(user=user)
    wishlist_ids = wishlist.values_list('restaurant_id', flat=True)
    res = Restaurant.objects.annotate(avg_rating=Avg('review__rating'))
    return render(request,'restaurants_to_explore.html', {'res':res, 'wishlist_ids': wishlist_ids,"user":user})


def place(request,id):
    if 'email' not in request.session:
        return redirect('login')
    res=Place.objects.get(id=id)
    reviews = Review.objects.filter(place=res)
    average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    average_rating = round(average_rating, 2)
    user = None
    wishlist_ids = []
    if 'email' in request.session:
        user = Userregister.objects.get(email=request.session['email'])
        wishlist_ids = list(Wishlist.objects.filter(user=user).values_list('place_id', flat=True))
    if request.method == "POST":
        review_text = request.POST.get('review')
        rating = request.POST.get('rating')
        rating = int(rating) if rating else None
        if not rating:
            return render(request, 'place.html', {'error': 'Please select rating', 'user':user, 'review_text':review_text, 'i':res, 'reviews':reviews, 'wishlist_ids': wishlist_ids, 'average_rating': average_rating})
        Review.objects.create(
            user=user,
            place=res,
            email=user.email,
            review=review_text,
            rating=int(rating)
        )
        return redirect('place', id=id)
    return render(request, 'place.html', {
        'i': res,
        'reviews': reviews,
        'wishlist_ids': wishlist_ids,
        'user':user,
        'average_rating': average_rating
    })

def food(request,id):
    if 'email' not in request.session:
        return redirect('login')
    res = Food.objects.get(id=id)
    shops = res.shops.all()
    reviews = Review.objects.filter(food=res)
    average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    average_rating = round(average_rating, 2)
    user = None
    wishlist_ids = []

    if 'email' in request.session:
        user = Userregister.objects.get(email=request.session['email'])
        wishlist_ids = list(Wishlist.objects.filter(user=user).values_list('food_id', flat=True))

    if request.method == "POST":
        review_text = request.POST.get('review')
        rating = request.POST.get('rating')
        rating = int(rating) if rating else None
        if not rating:
            return render(request, 'food.html', {
                'error': 'Please select rating',
                'review_text':review_text,
                'food': res,
                'reviews': reviews,
                'wishlist_ids':  wishlist_ids,
                'user':user,
                'shops': shops,
                'average_rating':average_rating

            })

        Review.objects.create(
            user=user,
            food=res,
            email=user.email,
            review=review_text,
            rating=int(rating)
        )

        return redirect('food', id=id)

    return render(request, 'food.html', {
        'i': res,
        'reviews': reviews,
        'wishlist_ids':  wishlist_ids,
        'user':user,
        'shops': shops,
        'average_rating':average_rating
    })

def hotel(request,id):
    if 'email' not in request.session:
        return redirect('login')
    res = Hotel.objects.get(id=id)
    branches = res.branches.all()
    single_branch = None
    if branches.count() == 1:
        single_branch = branches.first()
    reviews = Review.objects.filter(hotel=res)
    average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    average_rating = round(average_rating, 2)
    user = None
    wishlist_ids = []
    main_branch_exists = branches.filter(branch_name="Main Branch").exists()

    hero_images = []

    if branches.exists():
        for branch in branches:
            for img in branch.gallery.all():
                hero_images.append(img.image)

            if branch.image:
                hero_images.append(branch.image)
    else:
        for img in res.gallery.all():
            hero_images.append(img.image)

        if res.image:
            hero_images.append(res.image)



    if 'email' in request.session:
        user = Userregister.objects.get(email=request.session['email'])
        wishlist_ids = list(Wishlist.objects.filter(user=user).values_list('hotel_id', flat=True))

    if request.method == "POST":
        review_text = request.POST.get('review')
        rating = request.POST.get('rating')

        if not rating:
            return render(request, 'hotel.html', {
                'error': 'Please select rating',
                'review_text':review_text,
                'hotel': res,
                'reviews': reviews,
                'wishlist_ids': wishlist_ids,
                'user':user,
                'average_rating':average_rating,
                'branches': branches,
                'single_branch': single_branch,
                'main_branch_exists': main_branch_exists,
                'hero_images': hero_images,
            })

        Review.objects.create(
            user=user,
            hotel=res,
            email=user.email,
            review=review_text,
            rating=int(rating)
        )

        return redirect('hotel', id=id)

    return render(request, 'hotel.html', {
        'i': res,
        'reviews': reviews,
        'wishlist_ids': wishlist_ids,
        'user':user,
        'average_rating':average_rating,
        'branches': branches,
        'single_branch': single_branch,
        'main_branch_exists': main_branch_exists,
        'hero_images': hero_images,
    })

def restaurant(request,id):
    if 'email' not in request.session:
        return redirect('login')
    res = Restaurant.objects.get(id=id)
    branches = res.branches.all()
    single_branch = None
    if branches.count() == 1:
        single_branch = branches.first()
    reviews = Review.objects.filter(restaurant=res)
    average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    average_rating = round(average_rating, 2)
    user = None
    wishlist_ids = []
    hero_images = []

    if branches.exists():
        for branch in branches:
            for img in branch.gallery.all():
                hero_images.append(img.image)

            if branch.image:
                hero_images.append(branch.image)
    else:
        for img in res.gallery.all():
            hero_images.append(img.image)

        if res.image:
            hero_images.append(res.image)



    if 'email' in request.session:
        user = Userregister.objects.get(email=request.session['email'])
        wishlist_ids = list(Wishlist.objects.filter(user=user).values_list('restaurant_id', flat=True))

    if request.method == "POST":
        review_text = request.POST.get('review')
        rating = request.POST.get('rating')

        if not rating:
            return render(request, 'restaurant.html', {
                'error': 'Please select rating',
                'review_text':review_text,
                'restaurant': res,
                'reviews': reviews,
                'wishlist_ids': wishlist_ids,
                'user':user,
                'average_rating':average_rating,
                'branches': branches,
                'single_branch': single_branch,
                'hero_images': hero_images,
            })

        Review.objects.create(
            user=user,
            restaurant=res,
            email=user.email,
            review=review_text,
            rating=int(rating)
        )

        return redirect('restaurant', id=id)

    return render(request, 'restaurant.html', {
        'i': res,
        'reviews': reviews,
        'wishlist_ids': wishlist_ids,
        'user':user,
        'average_rating':average_rating,
        'branches': branches,
        'single_branch': single_branch,
        'hero_images': hero_images,
    })


def products_to_buy(request):
    if 'email' not in request.session:
        return redirect('login')
    user = Userregister.objects.get(email=request.session['email'])
    wishlist = Wishlist.objects.filter(user=user)
    wishlist_ids = wishlist.values_list('product_id', flat=True)
    res = Product.objects.annotate(avg_rating=Avg('review__rating'))
    return render(request,'products_to_buy.html', {'res':res, 'wishlist_ids': wishlist_ids,"user":user})

def product(request,id):
    if 'email' not in request.session:
        return redirect('login')
    res = Product.objects.get(id=id)
    shops = res.shops.all()
    reviews = Review.objects.filter(product=res)
    average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    average_rating = round(average_rating, 2)
    user = None
    wishlist_ids = []

    if 'email' in request.session:
        user = Userregister.objects.get(email=request.session['email'])
        wishlist_ids = list(Wishlist.objects.filter(user=user).values_list('product_id', flat=True))

    if request.method == "POST":
        review_text = request.POST.get('review')
        rating = request.POST.get('rating')
        rating = int(rating) if rating else None
        if not rating:
            return render(request, 'food.html', {
                'error': 'Please select rating',
                'review_text':review_text,
                'product': res,
                'reviews': reviews,
                'wishlist_ids':  wishlist_ids,
                'user':user,
                'shops': shops,
                'average_rating':average_rating

            })

        Review.objects.create(
            user=user,
            product=res,
            email=user.email,
            review=review_text,
            rating=int(rating)
        )

        return redirect('product', id=id)

    return render(request, 'food.html', {
        'i': res,
        'reviews': reviews,
        'wishlist_ids':  wishlist_ids,
        'user':user,
        'shops': shops,
        'average_rating':average_rating
    })


def wishlist(request):
    user = Userregister.objects.get(email=request.session['email'])
    place_items = Wishlist.objects.filter(user=user, place__isnull=False)
    food_items = Wishlist.objects.filter(user=user, food__isnull=False)
    hotel_items = Wishlist.objects.filter(user=user, hotel__isnull=False)
    shop_items = Wishlist.objects.filter(user=user, shop__isnull=False)
    product_items = Wishlist.objects.filter(user=user, product__isnull=False)
    restaurant_items = Wishlist.objects.filter(user=user, restaurant__isnull=False)




    return render(request, "wishlist.html", {
        "place_items": place_items,
        "food_items": food_items,
        "hotel_items": hotel_items,
        "shop_items":shop_items,
        "product_items":product_items,
        "restaurant_items":restaurant_items


    })



def toggle_wishlist(request):
    if request.method == "POST":
        user = Userregister.objects.get(email=request.session['email'])
        item_id = request.POST.get("id")
        item_type = request.POST.get("type") 

        if item_type == "place":
            obj = Place.objects.get(id=item_id)
            wishlist_item = Wishlist.objects.filter(user=user, place=obj)

            if wishlist_item.exists():
                wishlist_item.delete()
                return JsonResponse({"status": "removed"})
            else:
                Wishlist.objects.create(user=user, place=obj)
                return JsonResponse({"status": "added"})

        elif item_type == "food":
            obj = Food.objects.get(id=item_id)
            wishlist_item = Wishlist.objects.filter(user=user, food=obj)

            if wishlist_item.exists():
                wishlist_item.delete()
                return JsonResponse({"status": "removed"})
            else:
                Wishlist.objects.create(user=user, food=obj)
                return JsonResponse({"status": "added"})

        elif item_type == "hotel":
            obj = Hotel.objects.get(id=item_id)
            wishlist_item = Wishlist.objects.filter(user=user, hotel=obj)

            if wishlist_item.exists():
                wishlist_item.delete()
                return JsonResponse({"status": "removed"})
            else:
                Wishlist.objects.create(user=user, hotel=obj)
                return JsonResponse({"status": "added"})
        elif item_type == "product":
            obj = Product.objects.get(id=item_id)
            wishlist_item = Wishlist.objects.filter(user=user, product=obj)

            if wishlist_item.exists():
                wishlist_item.delete()
                return JsonResponse({"status": "removed"})
            else:
                Wishlist.objects.create(user=user, product=obj)
                return JsonResponse({"status": "added"})

        elif item_type == "shop":
            obj = Shop.objects.get(id=item_id)
            wishlist_item = Wishlist.objects.filter(user=user, shop=obj)

            if wishlist_item.exists():
                wishlist_item.delete()
                return JsonResponse({"status": "removed"})
            else:
                Wishlist.objects.create(user=user, shop=obj)
                return JsonResponse({"status": "added"})

        elif item_type == "restaurant":
            obj = Restaurant.objects.get(id=item_id)
            wishlist_item = Wishlist.objects.filter(user=user, restaurant=obj)

            if wishlist_item.exists():
                wishlist_item.delete()
                return JsonResponse({"status": "removed"})
            else:
                Wishlist.objects.create(user=user, restaurant=obj)
                return JsonResponse({"status": "added"})

def remove_wishlist(request, id):
    user = Userregister.objects.get(email=request.session['email'])
    item = get_object_or_404(Wishlist, id=id, user=user)
    item.delete()
    return redirect('wishlist')

def all_shops(request):
    if 'email' not in request.session:
        return redirect('login')
    user = Userregister.objects.get(email=request.session['email'])
    wishlist = Wishlist.objects.filter(user=user)
    wishlist_ids = wishlist.values_list('shop_id', flat=True)
    res = Shop.objects.annotate(avg_rating=Avg('review__rating'))
    return render(request,'all_shops.html', {'res':res, 'wishlist_ids': wishlist_ids,"user":user})


def shop(request, id):
    if 'email' not in request.session:
        return redirect('login')
    res = Shop.objects.get(id=id)
    reviews = Review.objects.filter(shop=res)
    average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    average_rating = round(average_rating, 2)
    foods = res.foods.all()   
    gallery = res.gallery.all()  
    user = None
    wishlist_ids = []

    if 'email' in request.session:
        user = Userregister.objects.get(email=request.session['email'])
        wishlist_ids = list(Wishlist.objects.filter(user=user).values_list('shop_id', flat=True))

    if request.method == "POST":
        review_text = request.POST.get('review')
        rating = request.POST.get('rating')
        rating = int(rating) if rating else None
        if not rating:
            return render(request, 'shop.html', {
                'error': 'Please select rating',
                'review_text':review_text,
                'shop': res,
                'foods': foods,
                'gallery': gallery,
                'reviews': reviews,
                'wishlist_ids': wishlist_ids,
                'user':user,
                'average_rating':average_rating
            })

        Review.objects.create(
            user=user,
            shop=res,
            email=user.email,
            review=review_text,
            rating=int(rating)
        )

        return redirect('shop', id=id)

    return render(request, 'shop.html', {
        'i': res,
        'reviews': reviews,
        'wishlist_ids': wishlist_ids,
        'user':user,
        'foods': foods,
        'gallery': gallery,
        'average_rating':average_rating
    })

def dashboard(request):
    email = request.session.get('email')
    user = Userregister.objects.get(email=email)
    return render(request,'dashboard.html',{"user":user})

def normalize_title(title):
    if title:
        return title.strip().title() 
    return title


def add_business(request):
    email = request.session.get('email')
    user = Userregister.objects.get(email=email)

    foods_database = Food.objects.all()
    products_database = Product.objects.all()

    user_id = request.session['email']
    owner = Userregister.objects.get(email=user_id)

    user_shops = Shop.objects.filter(owner=owner)
    hotels_database = Hotel.objects.filter(owner=owner)
    restaurants_database = Restaurant.objects.filter(owner=owner)

    shop = None
    shop_id = request.GET.get("shop_id")
    business_type = request.GET.get("business_type")
    existing_shop_id = request.POST.get("existing_shop_id")

    hotel_id = request.GET.get("hotel_id")
    restaurant_id = request.GET.get("restaurant_id")

    if request.method == "GET" and business_type == "hotel" and hotel_id:
        selected_hotel = Hotel.objects.filter(id=hotel_id, owner=owner).first()

        return render(request, "add_business.html", {
            "foods_database": foods_database,
            "products_database": products_database,
            "hotels_database": hotels_database,
            "restaurants_database": restaurants_database,
            "user_shops": user_shops,
            "user": user,
            "selected_business_type": "hotel",
            "selected_hotel_id": hotel_id,
            "selected_hotel": selected_hotel,
        })

    if request.method == "GET" and business_type == "restaurant" and restaurant_id:
        selected_restaurant = Restaurant.objects.filter(id=restaurant_id, owner=owner).first()

        return render(request, "add_business.html", {
            "foods_database": foods_database,
            "products_database": products_database,
            "hotels_database": hotels_database,
            "restaurants_database": restaurants_database,
            "user_shops": user_shops,
            "user": user,
            "selected_business_type": "restaurant",
            "selected_restaurant_id": restaurant_id,
            "selected_restaurant": selected_restaurant,
        })

    if request.method == "GET" and shop_id:
        selected_shop = Shop.objects.filter(id=shop_id, owner=owner).first()
        call = request.GET.get("type")

        return render(request, "add_business.html", {
            "call": call,
            "foods_database": foods_database,
            "products_database": products_database,
            "hotels_database": hotels_database,
            "restaurants_database": restaurants_database,
            "shop_id": shop_id,
            "selected_shop": selected_shop,
            "user_shops": user_shops,
            "user": user,
        })

    if request.method == "POST":
        business_type = request.POST.get("business_type")
        shop_id = request.POST.get("shop_id")

        if business_type == "food" or business_type == "product":
            shop_title = request.POST.get("shop_title")
            shop_title = normalize_title(shop_title)

            existing_shop = Shop.objects.filter(
                owner=owner,
                title__iexact=shop_title
            ).first()

            if existing_shop:
                return render(request, "add_business.html", {
                    "message": "Shop already exists! Add items under it instead.",
                    "foods_database": foods_database,
                    "products_database": products_database,
                    "hotels_database": hotels_database,
                    "restaurants_database": restaurants_database,
                    "user_shops": user_shops,
                    "user": user,
                })

        if business_type == "food":
            existing_food_id = request.POST.get("existing_food_id")

            if existing_food_id:
                food = Food.objects.get(id=existing_food_id)
                food.owners.add(owner)
            else:
                food = Food.objects.create(
                    title=normalize_title(request.POST.get("food_title")),
                    image=request.FILES.get("food_image"),
                    description=request.POST.get("food_description")
                )
                food.owners.add(owner)

            if existing_shop_id:
                shop = Shop.objects.get(id=existing_shop_id, owner=owner)
            elif shop_id:
                shop = Shop.objects.get(id=shop_id, owner=owner)
            else:
                shop = Shop.objects.create(
                    owner=owner,
                    title=normalize_title(request.POST.get("shop_title")),
                    image=request.FILES.get("shop_image"),
                    address=request.POST.get("shop_address"),
                    description=request.POST.get("shop_description"),
                )

            shop.foods.add(food)

            for img in request.FILES.getlist("shop_gallery"):
                ShopImage.objects.create(shop=shop, image=img)

        elif business_type == "product":
            existing_product_id = request.POST.get("existing_product_id")

            if existing_product_id:
                product = Product.objects.get(id=existing_product_id)
                product.owners.add(owner)
            else:
                product = Product.objects.create(
                    title=normalize_title(request.POST.get("product_title")),
                    image=request.FILES.get("product_image"),
                    description=request.POST.get("product_description")
                )
                product.owners.add(owner)

            if existing_shop_id:
                shop = Shop.objects.get(id=existing_shop_id, owner=owner)
            elif shop_id:
                shop = Shop.objects.get(id=shop_id, owner=owner)
            else:
                shop = Shop.objects.create(
                    owner=owner,
                    title=normalize_title(request.POST.get("shop_title")),
                    image=request.FILES.get("shop_image"),
                    address=request.POST.get("shop_address"),
                    description=request.POST.get("shop_description"),
                )

            shop.products.add(product)

            for img in request.FILES.getlist("shop_gallery"):
                ShopImage.objects.create(shop=shop, image=img)

        elif business_type == "hotel":
            existing_hotel_id = request.POST.get("existing_hotel_id")

            if existing_hotel_id:
                hotel = Hotel.objects.get(id=existing_hotel_id, owner=owner)

                hotel_branch = HotelBranch.objects.create(
                    hotel=hotel,
                    branch_name=request.POST.get("hotel_branch_name"),
                    address=request.POST.get("hotel_branch_address"),
                    image=request.FILES.get("hotel_branch_image")
                )

                for img in request.FILES.getlist("hotel_branch_gallery"):
                    HotelBranchImage.objects.create(
                        branch=hotel_branch,
                        image=img
                    )

            else:
                hotel = Hotel.objects.create(
                    owner=owner,
                    title=normalize_title(request.POST.get("hotel_title")),
                    image=request.FILES.get("hotel_image"),
                    address=request.POST.get("hotel_address"),
                    description=request.POST.get("hotel_description"),
                )

                HotelBranch.objects.create(
                    hotel=hotel,
                    branch_name="Main Branch",
                    address=request.POST.get("hotel_address"),
                    image=request.FILES.get("hotel_image")
                )

                for img in request.FILES.getlist("hotel_gallery"):
                    HotelImage.objects.create(hotel=hotel, image=img)

        elif business_type == "restaurant":
            existing_restaurant_id = request.POST.get("existing_restaurant_id")

            if existing_restaurant_id:
                restaurant = Restaurant.objects.get(
                    id=existing_restaurant_id,
                    owner=owner
                )

                restaurant_branch = RestaurantBranch.objects.create(
                    restaurant=restaurant,
                    branch_name=request.POST.get("restaurant_branch_name"),
                    address=request.POST.get("restaurant_branch_address"),
                    image=request.FILES.get("restaurant_branch_image")
                )

                for img in request.FILES.getlist("restaurant_branch_gallery"):
                    RestaurantBranchImage.objects.create(
                        branch=restaurant_branch,
                        image=img
                    )

            else:
                restaurant = Restaurant.objects.create(
                    owner=owner,
                    title=normalize_title(request.POST.get("restaurant_title")),
                    image=request.FILES.get("restaurant_image"),
                    address=request.POST.get("restaurant_address"),
                    description=request.POST.get("restaurant_description"),
                )

                RestaurantBranch.objects.create(
                    restaurant=restaurant,
                    branch_name="Main Branch",
                    address=request.POST.get("restaurant_address"),
                    image=request.FILES.get("restaurant_image")
                )

                for img in request.FILES.getlist("restaurant_gallery"):
                    RestaurantImage.objects.create(
                        restaurant=restaurant,
                        image=img
                    )

        return redirect("business_listing")

    return render(request, "add_business.html", {
        "foods_database": foods_database,
        "products_database": products_database,
        "hotels_database": hotels_database,
        "restaurants_database": restaurants_database,
        "user_shops": user_shops,
        "user": user,
        "selected_business_type": business_type,
        "selected_hotel_id": hotel_id,
        "selected_restaurant_id": restaurant_id,
    })


   
    

def delete_business(request, type, id):
    user_id = request.session.get("email")
    owner = get_object_or_404(Userregister, email=user_id)

    shop_id = request.GET.get("shop_id")

    if type == "shop":
        shop = get_object_or_404(Shop, id=id, owner=owner)

        for food in shop.foods.all():
            shop.foods.remove(food)

            other_shops = Shop.objects.filter(owner=owner, foods=food).exclude(id=shop.id)
            if not other_shops.exists():
                food.owners.remove(owner)

        for product in shop.products.all():
            shop.products.remove(product)

            other_shops = Shop.objects.filter(owner=owner, products=product).exclude(id=shop.id)
            if not other_shops.exists():
                product.owners.remove(owner)

        shop.delete()

    elif type == "food":
        food = get_object_or_404(Food, id=id)
        shop = get_object_or_404(Shop, id=shop_id, owner=owner)

        shop.foods.remove(food)

        other_shops = Shop.objects.filter(owner=owner, foods=food)
        if not other_shops.exists():
            food.owners.remove(owner)

    elif type == "product":
        product = get_object_or_404(Product, id=id)
        shop = get_object_or_404(Shop, id=shop_id, owner=owner)

        shop.products.remove(product)

        other_shops = Shop.objects.filter(owner=owner, products=product)
        if not other_shops.exists():
            product.owners.remove(owner)


    elif type == "hotel":
        hotel = get_object_or_404(Hotel, id=id, owner=owner)
        hotel.delete()  

    elif type == "hotel_branch":
        branch = get_object_or_404(HotelBranch, id=id, hotel__owner=owner)
        branch.delete()

    
    elif type == "restaurant":
        restaurant = get_object_or_404(Restaurant, id=id, owner=owner)
        restaurant.delete()  

    elif type == "restaurant_branch":
        branch = get_object_or_404(RestaurantBranch, id=id, restaurant__owner=owner)
        branch.delete()

    return redirect("business_listing")


def business_listing(request):
    email = request.session.get('email')
    user = Userregister.objects.get(email=email)
    user_id = request.session.get("email")
    owner = Userregister.objects.get(email=user_id)
    shops = Shop.objects.filter(owner=owner).prefetch_related(
        Prefetch("foods",queryset=Food.objects.filter(owners=owner), to_attr="filtered_foods"),
        Prefetch("products",queryset=Product.objects.filter(owners=owner), to_attr="filtered_products"),"gallery")

    hotels = Hotel.objects.filter(owner=owner).prefetch_related(
        "gallery",
        Prefetch(
            "branches",
            queryset=HotelBranch.objects.prefetch_related("gallery")
        )
    )


    restaurants = Restaurant.objects.filter(owner=owner).prefetch_related(
        "gallery",
        Prefetch(
            "branches",
            queryset=RestaurantBranch.objects.prefetch_related("gallery")
        )
    )


    context = {
        "shops": shops,
        "hotels": hotels,
        "restaurants": restaurants,
        "user":user
    }

    return render(request, "business_listing.html", context)



def normalize_query(query):
    query = query.lower().strip()
    query = query.replace('&', ' and ')
    query = re.sub(r'[^\w\s]', ' ', query)
    query = re.sub(r'\s+', ' ', query)
    return query


def calculate_score(obj, fields, query, words):
    score = 0

    for field in fields:
        value = getattr(obj, field, '')
        if not value:
            continue

        value = value.lower()

 
        if query in value:
            score += 100

    
        if value.startswith(query):
            score += 50

    
        for word in words:
            if word in value:
                score += 10

        
        if field == 'title':
            score *= 2

    return score


def build_q(fields, words):
    q = Q()
    for word in words:
        temp = Q()
        for field in fields:
            temp |= Q(**{f"{field}__icontains": word})
        q &= temp
    return q


def search(request):
    query = request.GET.get('q')

    if not query:
        return redirect(request.META.get('HTTP_REFERER', 'index'))

    query = normalize_query(query)
    words = query.split()

 
    if len(query) < 4 or all(len(w) < 2 for w in words):
        messages.warning(request, "Please enter at least 1 word!")
        return redirect(request.META.get('HTTP_REFERER', 'index'))

  
    words = [w for w in words if len(w) >= 2]

    if not words:
        messages.warning(request, "No result found!")
        return redirect(request.META.get('HTTP_REFERER', 'index'))


    MIN_SCORE = 80 if len(words) == 1 else 50

    def search_model(model, fields, model_name):
        if len(words) == 1:
            queryset = model.objects.filter(title__icontains=words[0])
        else:
            queryset = model.objects.filter(build_q(fields, words))

        results = []
        for obj in queryset:
            score = calculate_score(obj, fields, query, words)

            if score >= MIN_SCORE:
                results.append({
                    'type': model_name,
                    'id': obj.id,
                    'score': score
                })

        return results

    results = []

    results += search_model(Place, ['title', 'history', 'introduction'], 'place')
    results += search_model(Food, ['title', 'description'], 'food')
    results += search_model(Hotel, ['title', 'description'], 'hotel')
    results += search_model(Shop, ['title', 'description'], 'shop')
    results += search_model(Product, ['title', 'description'], 'product')
    results += search_model(Restaurant, ['title', 'description'], 'restaurant')


    if not results:
        messages.warning(request, "No result found!")
        return redirect(request.META.get('HTTP_REFERER', 'index'))

    results = sorted(results, key=lambda x: x['score'], reverse=True)

    best = results[0]

    return redirect(best['type'], id=best['id'])



def subscribe_newsletter(request):
    if request.method == "POST":
        email_session = request.session.get('email')
        if not email_session:
            messages.error(request, "Please login first to subscribe to newsletter.")
            return redirect('login')
        email = request.POST.get('email')
        if email_session != email:
            messages.error(request, "Please login first with that email id to subscribe to newsletter.")
            return redirect('login')

        user = Userregister.objects.get(email=email) 
        if NewsletterSubscriber.objects.filter(email=email).exists():
            messages.warning(request, "You are already subscribed!")
            return redirect('index')
        NewsletterSubscriber.objects.create(
            user=user,
            email=email
        )
        user.newsletter = True
        user.save()
        messages.success(request, "Successfully subscribed to newsletter!")
        return redirect('index')


def edit_profile(request):
    email_session = request.session.get('email')

    if not email_session:
        messages.error(request, "Please login first.")
        return redirect('login')

    try:
        user = Userregister.objects.get(email=email_session)
    except Userregister.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('login')

    if request.method == "POST":

        # Readonly fields (still assign to be safe)
        user.firstname = request.POST.get('firstname')
        user.email = request.POST.get('email')

        # Optional fields (safe if empty)
        user.lastname = request.POST.get('lastname') or None
        user.contact = request.POST.get('contact') or None
        user.alternate_contact = request.POST.get('alternate_contact') or None
        user.birthday = request.POST.get('birthday') or None
        user.age = request.POST.get('age') or None
        user.social_link = request.POST.get('social_link') or None
        user.gender = request.POST.get('gender') or None
        user.address = request.POST.get('address') or None
        user.bio = request.POST.get('bio') or None

        # Image upload
        if request.FILES.get('photo'):
            user.photo = request.FILES.get('photo')

        # Newsletter checkbox logic
        newsletter_checked = request.POST.get('newsletter') == 'yes'
        user.newsletter = newsletter_checked

        if newsletter_checked:
            # Subscribe if not already
            if not NewsletterSubscriber.objects.filter(email=user.email).exists():
                NewsletterSubscriber.objects.create(
                    email=user.email,
                    user=user
                )
            user.newsletter = True
        else:
            # Unsubscribe if exists
            NewsletterSubscriber.objects.filter(email=user.email).delete()
            user.newsletter = False

        user.save()

        messages.success(request, "Profile updated successfully!")
        return redirect('edit_profile')

    return render(request, 'edit_profile.html', {'user': user})