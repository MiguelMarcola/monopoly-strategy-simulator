from django.urls import path

from game.views import simulate

urlpatterns = [
    path('simular', simulate),
]
