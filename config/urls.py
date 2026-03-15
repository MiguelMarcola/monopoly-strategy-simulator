from django.urls import path, include

urlpatterns = [
    path('jogo/', include('game.urls')),
]
