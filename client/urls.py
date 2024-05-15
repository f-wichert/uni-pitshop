from django.urls import path

from . import views

app_name = "client"
urlpatterns = [
    # Landing Page
    path("", views.landing, name="landing"),
    # Produktauswahl
    path("produktauswahl/", views.produktauswahl_main_page, name="produktauswahl"),
    path("produktauswahl/laserschnitt/", views.produktauswahl_laserschnitt, name="laserschnitt"),
    path("produktauswahl/materialkauf/", views.produktauswahl_materialkauf, name="materialkauf"),
    path("materialkauf_table/", views.materialkauf_table, name="materialkauf_table"),
    path("media/preview_images/<str:img>", views.preview_images, name="preview_image"),
    # Login
    path("login/", views.login, name="login"),
    # Meine Aufträge
    path("my-orders/", views.my_orders, name="my-orders"),
    path("my-orders/<int:ID>", views.my_orders, name="my-orders"),
    path("my-orders-entries/", views.my_orders_entries, name="my-orders-entries"),
    # Controlling
    path("controlling/", views.controlling, name="controlling"),
    path("controlling/filter", views.controlling_filter, name="controlling_filter"),
    path(
        "controlling/billing_modal",
        views.controlling_billing_modal,
        name="controlling_billing_modal",
    ),
    path(
        "controlling/auto_billing",
        views.controlling_automatic_billing_search,
        name="controlling_auto_billing",
    ),
    path("controlling/print", views.controlling_print, name="controlling_print"),
    # Cart
    path("cart/table", views.cart_table, name="cart_table"),
    path("get_lasercut_file/<int:lasercut_id>", views.get_lasercut_file, name="get_lasercut_file"),
    # Orders
    path("orders/", views.orders_overview),
    path("orders/filtered_orders", views.filtered_orders, name="filtered_orders"),
    path("orders/payment_state/", views.orders_payment_state),
    path("orders/quittung/", views.orders_quittung),
    path("orders/invoice_data/", views.orders_invoice_data),
    path("orders/invoice/", views.orders_invoice),
    path("orders/quittung_data/", views.orders_quittung_data),
    path("orders/material_data_for_lasercut/", views.orders_material_data_for_lasercut),
    # Messenger
    path("messenger/get_messages/", views.get_messages),
    path("messenger/get_messages_user/", views.get_messages_user),
]
