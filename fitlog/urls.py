from django.urls import path

from . import views

urlpatterns = [
    path("me/settings/", views.me_settings, name="fitlog-me-settings"),
    path("me/diary/", views.me_diary, name="fitlog-me-diary"),
    path("me/custom-foods/", views.me_custom_foods, name="fitlog-me-custom-foods"),
    path("me/water/", views.me_water, name="fitlog-me-water"),
    path("me/recipes/", views.me_recipes, name="fitlog-me-recipes"),
]
