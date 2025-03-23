from django.urls import path
from ecommerceapp import views

urlpatterns = [
    path('',views.index,name="index"),
    path('contact/',views.contact,name="contact"),
    path('about',views.about,name="about"),
    path('profile',views.profile,name="profile"),
    path('checkout/',views.checkout,name="Checkout"),
    path('term-and-condition/',views.termandcondition,name="term-and-condition"),
    path('privacy-policy/',views.privacypolicy,name="privacy-policy"),
    path('handlerequest/',views.handlerequest,name="HandleRequest"),
]