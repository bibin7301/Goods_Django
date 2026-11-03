from django.urls import path
from . import views

urlpatterns = [
    path("", views.cart, name="cart"),
    path("add_to_cart/<int:product_id>", views.add_to_cart, name="add_to_cart"),
    path("increase/<int:item_id>/", views.increase_quantity, name="increase_quantity"),
    path("decrease/<int:item_id>/", views.decrease_quantity, name="decrease_quantity"),
    path("remove/<int:item_id>/", views.remove_from_cart, name="remove_from_cart"),
    path("place-order/", views.place_order, name="place_order"),
    path("payment/<int:order_id>/", views.payment, name="payment"),
    path("payment/verify/", views.payment_verify, name="payment_verify"),
    path("payment/cancel/<int:order_id>/", views.cancel_payment, name="cancel_payment"),
    path("orders/", views.order_view, name="orders"),
]
