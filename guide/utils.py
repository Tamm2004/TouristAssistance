# guide/utils.py
from guide.models import Place
from guide.models import Food
from guide.models import Hotel
from guide.models import Product
from guide.models import Shop
from guide.models import FAQ
from guide.models import Restaurant
from guide.models import Recommendation
from guide.models import WeatherData
from datetime import datetime
from django.db.models import Avg
from guide.models import Review
import re
from difflib import get_close_matches


def get_avg_rating(obj):
    if isinstance(obj, Place):
        reviews = Review.objects.filter(place=obj)
    elif isinstance(obj, Food):
        reviews = Review.objects.filter(food=obj)
    elif isinstance(obj, Hotel):
        reviews = Review.objects.filter(hotel=obj)
    elif isinstance(obj, Product):
        reviews = Review.objects.filter(product=obj)
    elif isinstance(obj, Shop):
        reviews = Review.objects.filter(shop=obj)
    elif isinstance(obj, Restaurant):
        reviews = Review.objects.filter(restaurant=obj)
    else:
        return 0
    if reviews.exists():
        avg_rating=reviews.aggregate(Avg('rating'))['rating__avg']
        if avg_rating >= 4:
            sentiment = "Excellent ⭐"
        elif avg_rating >= 3:
            sentiment = "Good 👍"
        elif avg_rating >= 2:
            sentiment = "Average 😐"
        else:
            sentiment = "Poor 👎"
        return f"Average Rating: {round(avg_rating,1)} ⭐ ({sentiment})"
    return "No ratings yet"


def normalize_text(text):
    text = text.lower()
    text = text.replace("how's", "how is")
    text = text.replace("what's", "what is")
    text = text.replace("who's", "who is")
    text = text.replace("i'm", "i am")
    text = text.replace("you're", "you are")
    # Remove punctuation
    text = re.sub(r'[^\w\s]', '', text)
    return text.strip()

def clean_text(text):
    STOPWORDS = ["what", "is", "the", "are", "of", "does", "when", "a", "an", "to"]
    text = text.lower()
    words = re.findall(r'\w+', text)
    filtered = [w for w in words if w not in STOPWORDS]
    return filtered

def match_faq(user_message):
    user_words = normalize_text(user_message)
    user_words = clean_text(user_words)
    faqs = FAQ.objects.all()

    best_match = None
    best_score = 0

    for faq in faqs:
        faq_words = normalize_text(faq.question)
        faq_words = clean_text(faq_words)
        # count common words
        common = set(user_words) & set(faq_words)
        score = len(common)
        if score > best_score:
            best_score = score
            best_match = faq
    if best_score >= 3:
        return best_match.answer
    return None


def fuzzy_match(user_message):
    faqs = FAQ.objects.all()
    questions = [faq.question.lower() for faq in faqs]

    match = get_close_matches(user_message.lower(), questions, n=1, cutoff=0.6)
    if match:
        return FAQ.objects.get(question__iexact=match[0]).answer
    return None


def find_entity(user_message):
    user_words = normalize_text(user_message)
    user_words = clean_text(user_words)

    models = [
        ("place", Place),
        ("food", Food),
        ("hotel", Hotel),
        ("product", Product),
        ("shop", Shop),
        ("restaurant", Restaurant),

    ]

    all_objects = []
    for obj_type, model in models:
        for obj in model.objects.all():
            words = normalize_text(obj.title)
            all_objects.append((obj_type, obj, words, obj.title.lower()))

    # 1. EXACT MATCH

    for obj_type, obj, words, title in all_objects:
        if " ".join(user_words) == title:
            return (obj_type, obj)

    # 2. SCORING MATCH

    best_match = None
    best_score = 0

    for obj_type, obj, words, _ in all_objects:
        common = set(user_words) & set(words)
        score = len(common)

        if obj_type == "food":
            score += 0.5

        if score > best_score:
            best_score = score
            best_match = (obj_type, obj)

    if best_score >= 1:
        return best_match

    titles = [title for _, _, _, title in all_objects]

    match = get_close_matches(
        " ".join(user_words),
        titles,
        n=1,
        cutoff=0.5
    )

    if match:
        for obj_type, obj, _, title in all_objects:
            if title == match[0]:
                return (obj_type, obj)

    return (None, None)

def summarize_text(html_text, max_sentences=3):
    if not html_text:
        return ""
    text = re.sub(r'<h[1-6].*?>.*?</h[1-6]>', '', str(html_text), flags=re.DOTALL)
    text = re.sub('<.*?>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    sentences = re.split(r'(?<=[.!?]) +', text)
    return " ".join(sentences[:max_sentences])

import re

def handle_greetings(msg):
    responses = []

    # Normalize
    msg = msg.lower()
    msg = re.sub(r'[^\w\s]', '', msg)

    greetings = ["hi", "hello", "hey", "hii", "heyy"]
    how_are_you_patterns = [
        "how are you", "how is you", "how r you",
        "how you", "hows you", "how are u", "how u"
    ]
    help_patterns = [
        "help", "help me", "what can you do",
        "what you can do", "options", "guide me"
    ]
    identity_patterns = [
        "who are you", "what are you", "tell me about you"
    ]

    thanks_patterns = ["thanks", "thank you", "thx"]
    bye_patterns = ["bye", "goodbye", "see you"]

    
    if "good morning" in msg:
        responses.append((85, {
            "type": "text",
            "data": "Good morning ☀️ How can I help you today?"
        }))

    if "good afternoon" in msg:
        responses.append((85, {
            "type": "text",
            "data": "Good afternoon 😊 What can I do for you?"
        }))

    if "good evening" in msg:
        responses.append((85, {
            "type": "text",
            "data": "Good evening 🌙 Need any travel help?"
        }))

    
    if any(word in msg for word in bye_patterns):
        responses.append((90, {
            "type": "text",
            "data": "Goodbye 👋 Have a great trip!"
        }))

    
    if any(word in msg for word in thanks_patterns):
        responses.append((80, {
            "type": "text",
            "data": "You're welcome 😊 Happy to help!"
        }))


    if any(phrase in msg for phrase in how_are_you_patterns):
        responses.append((88, {
            "type": "text",
            "data": "I'm doing great 😊 Thanks for asking! How can I assist you today?"
        }))


    if any(word in msg.split() for word in greetings):
        responses.append((60, {
            "type": "text",
            "data": "Hello! 👋 Welcome to Tourist Assistant."
        }))


    if any(phrase in msg for phrase in help_patterns):
        responses.append((70, {
            "type": "list",
            "title": "I can help you with:",
            "data": [
                "🏛️ Places to visit",
                "🍛 Famous food",
                "🏨 Hotels to stay",
                "🍽️ Restaurants to explore",
                "🛍️ Products to buy",
                "🏬 Shops to explore",
                "🌦️ Weather updates",
                "Much more"
            ]
        }))


    if any(phrase in msg for phrase in identity_patterns):
        responses.append((65, {
            "type": "text",
            "data": "I'm your Tourist Assistant 🤖 helping you explore places, food, hotels, restaurants and more!"
        }))


    if responses:
        responses = sorted(responses, key=lambda x: x[0], reverse=True)
        return responses[0][1]

    return None


def get_fallback_recommendations(item_type, exclude_ids=[], limit=5):

    if item_type == "place":
        queryset = Place.objects.exclude(id__in=exclude_ids)

    elif item_type == "food":
        queryset = Food.objects.exclude(id__in=exclude_ids)

    elif item_type == "hotel":
        queryset = Hotel.objects.exclude(id__in=exclude_ids)

    elif item_type == "product":
        queryset = Product.objects.exclude(id__in=exclude_ids)

    elif item_type == "shop":
        queryset = Shop.objects.exclude(id__in=exclude_ids)

    elif item_type == "restaurant":
        queryset = Restaurant.objects.exclude(id__in=exclude_ids)

    else:
        return []

    return [obj.title for obj in queryset[:limit]]

def get_bot_response(user_message, request):
    msg = normalize_text(user_message)
    words = clean_text(msg)

    candidates = []

    # ADD RESPONSE WITH SCORE
    def add_candidate(score, response):
        candidates.append((score, response))

 
    # 1. GREETINGS 

    greeting_response = handle_greetings(msg)
    if greeting_response:
        add_candidate(90, greeting_response)


    # 2. WEATHER

    if "weather" in msg or "temperature" in msg:
        weather = WeatherData.objects.filter(city__iexact="amritsar").first()
        if weather:
            add_candidate(85, {
                "type": "paragraph",
                "data": f"🌤️ Weather in {weather.city.title()}:\n"
                        f"🌡️ {weather.temperature}°C (Feels {weather.feels_like}°C)\n"
                        f"💧 Humidity: {weather.humidity}%\n"
                        f"🌬️ Wind: {weather.wind_speed} km/h\n"
                        f"📝 {weather.description}"
            })

    # 3. FAQ MATCH 

    faq_answer = match_faq(user_message)
    if faq_answer:
        add_candidate(95, {
            "type": "paragraph",
            "data": faq_answer
        })

    fuzzy_answer = fuzzy_match(user_message)
    if fuzzy_answer:
        add_candidate(80, {
            "type": "paragraph",
            "data": fuzzy_answer
        })



    # HIGHEST RATED 

    if "highest rated" in msg or "top rated" in msg or "best rated" in msg:

        if "hotel" in msg:
            hotels = Hotel.objects.annotate(avg=Avg('review__rating')).order_by('-avg')[:5]

            return {
                "type": "content",
                "data": "🏨 Top rated hotels:",
                "list": [h.title for h in hotels if h.avg]
            }

        elif "place" in msg:
            places = Place.objects.annotate(avg=Avg('review__rating')).order_by('-avg')[:5]

            return {
                "type": "content",
                "data": "🏛️ Top rated places:",
                "list": [p.title for p in places if p.avg]
            }

        elif "food" in msg:
            foods = Food.objects.annotate(avg=Avg('review__rating')).order_by('-avg')[:5]

            return {
                "type": "content",
                "data": "🍛 Top rated food:",
                "list": [f.title for f in foods if f.avg]
            }

        elif "restaurant" in msg:
            restaurants = Restaurant.objects.annotate(avg=Avg('review__rating')).order_by('-avg')[:5]

            return {
                "type": "content",
                "data": "🍽️ Top rated restaurants:",
                "list": [r.title for r in restaurants if r.avg]
            }

        elif "product" in msg:
            products = Product.objects.annotate(avg=Avg('review__rating')).order_by('-avg')[:5]

            return {
                "type": "content",
                "data": "🛍️ Top rated products:",
                "list": [p.title for p in products if p.avg]
            }

        elif "shop" in msg:
            shops = Shop.objects.annotate(avg=Avg('review__rating')).order_by('-avg')[:5]

            return {
                "type": "content",
                "data": "🏬 Top rated shops:",
                "list": [s.title for s in shops if s.avg]
            }

    # 4. ENTITY DETECTION

    obj_type, obj = find_entity(user_message)

    if obj:
        score = 70

        if "history" in msg and obj_type == "place":
            score += 20
            text = getattr(obj, "history", "")
        elif "about" in msg or "introduction" in msg:
            score += 15
            text = getattr(obj, "introduction", None) or getattr(obj, "description", "")
        elif "review" in msg or "rating" in msg:
            score += 20
            add_candidate(score, {
                "type": "paragraph",
                "data": get_avg_rating(obj)
            })
            text = None
        else:
            text = getattr(obj, "introduction", None) or getattr(obj, "description", "")

        if text:
            add_candidate(score, {
                "type": "paragraph",
                "data": summarize_text(text)
            })


    # 5. RECOMMENDATION 

    def get_top_items(model, fields, query, limit=5):
        results = []

        IGNORE_WORDS = ["famous", "best", "top", "recommend", "suggest","shop", "shops", "product", "products",
        "hotel", "hotels", "place", "places","food", "foods","restaurant","restaurants"]

        filtered_words = [w for w in words if w not in IGNORE_WORDS]

        for obj in model.objects.all():
            score = 0
            text_data = " ".join([str(getattr(obj, f, "")).lower() for f in fields])

            if not filtered_words:
                score += 1

            for w in filtered_words:
                if w in text_data:
                    score += 10

            if hasattr(obj, "title") and any(w in obj.title.lower() for w in filtered_words):
                score += 30

            if score > 0:
                results.append((obj, score))

        if not results:
            return list(model.objects.all()[:limit])

        results = sorted(results, key=lambda x: x[1], reverse=True)
        return [r[0] for r in results[:limit]]

    if any(x in msg for x in ["recommend", "suggest", "famous", "best"]):

        if "place" in msg:
            items = get_top_items(Place, ["title", "history", "introduction"], msg)
            add_candidate(75, {
                "type": "content",
                "data": "🏛️ Famous places to visit:",
                "list": [i.title for i in items]
            })

        elif "food" in msg:
            items = get_top_items(Food, ["title", "description"], msg)
            add_candidate(75, {
                "type": "content",
                "data": "🍛 Must-try food:",
                "list": [i.title for i in items]
            })

        elif "hotel" in msg:
            items = get_top_items(Hotel, ["title", "description"], msg)
            add_candidate(75, {
                "type": "content",
                "data": "🏨 Best hotels:",
                "list": [i.title for i in items]
            })

        elif "product" in msg:
            items = get_top_items(Product, ["title", "description"], msg)
            add_candidate(75, {
                "type": "content",
                "data": "🛍️ Popular products to buy:",
                "list": [i.title for i in items]
            })

        elif "shop" in msg:
            items = get_top_items(Shop, ["title", "description"], msg)
            add_candidate(75, {
                "type": "content",
                "data": "🏬 Popular shops to explore:",
                "list": [i.title for i in items]
            })

        elif "restaurant" in msg:
            items = get_top_items(Restaurant, ["title", "description"], msg)
            add_candidate(75, {
                "type": "content",
                "data": "🍽️ Popular restaurants to explore:",
                "list": [i.title for i in items]
            })


    # SHOP INTENT

    
    if ("shop" in msg or "shops" in msg or "place" in msg or "places" in msg or "where" in msg) and (obj_type=="food" or obj_type=="product"):
        shops = obj.shops.all()[:5] if hasattr(obj, "shops") else []
        text=summarize_text(obj.description)
        if shops:
            return {
            "type": "content",
            "data":f"Best places to eat {obj.title}",
            "list": [shop.title for shop in shops],
            "more": "You can explore more in that particular food page section."}
        else:
            return {
            "type": "paragraph",
            "data": summarize_text(obj.description)}


    # 6. CATEGORY BASED

    if "religious" in msg and "place" in msg:
        places = Place.objects.filter(categories__name__icontains="religious")[:5]
        add_candidate(60, {
            "type": "list",
            "title": "Religious Places",
            "data": [p.title for p in places]
        })

    if "place" in msg:
        places = Place.objects.all()[:5]
        add_candidate(50, {
            "type": "list",
            "title": "Places to visit",
            "data": [p.title for p in places]
        })

    if "food" in msg:
        foods = Food.objects.all()[:5]
        add_candidate(50, {
            "type": "list",
            "title": "Famous Food",
            "data": [f.title for f in foods]
        })

    if "product" in msg:
        products = Product.objects.all()[:5]
        add_candidate(50, {
            "type": "list",
            "title": "Famous Products",
            "data": [f.title for f in products]
        })

    if "shop" in msg:
        shops = Shop.objects.all()[:5]
        add_candidate(30, {
            "type": "list",
            "title": "Famous Shops",
            "data": [f.title for f in shops]
        })

    if "restaurant" in msg:
        restaurants = Restaurant.objects.all()[:5]
        add_candidate(30, {
            "type": "list",
            "title": "Famous Restaurants",
            "data": [f.title for f in restaurants]
        })



    # 7. FINAL DECISION

    if candidates:
        candidates = sorted(candidates, key=lambda x: x[0], reverse=True)
        return candidates[0][1]

    return {
        "type": "text",
        "data": "Sorry, I didn't understand that."
    }
