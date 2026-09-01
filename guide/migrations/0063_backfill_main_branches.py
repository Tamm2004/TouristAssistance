from django.db import migrations


MAIN_BRANCH = "Main Branch"


def create_missing_main_branches(apps, schema_editor):
    Hotel = apps.get_model("guide", "Hotel")
    HotelBranch = apps.get_model("guide", "HotelBranch")
    Restaurant = apps.get_model("guide", "Restaurant")
    RestaurantBranch = apps.get_model("guide", "RestaurantBranch")

    for hotel in Hotel.objects.filter(branches__isnull=True):
        HotelBranch.objects.create(
            hotel=hotel,
            branch_name=MAIN_BRANCH,
            address="",
            image=hotel.image.name or "",
        )

    for restaurant in Restaurant.objects.filter(branches__isnull=True):
        RestaurantBranch.objects.create(
            restaurant=restaurant,
            branch_name=MAIN_BRANCH,
            address=restaurant.address,
            image=restaurant.image.name or "",
        )


class Migration(migrations.Migration):
    dependencies = [
        ("guide", "0062_hotelbranch_hotelbranchimage_restaurantbranch_and_more"),
    ]

    operations = [
        migrations.RunPython(
            create_missing_main_branches,
            migrations.RunPython.noop,
        ),
    ]
