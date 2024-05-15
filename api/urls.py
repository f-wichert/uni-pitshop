from typing import List

from django.urls import URLPattern, path

from . import views

app_name = "api"
urlpatterns: List[URLPattern] = [
    path("auth/", views.auth, name="auth"),
    path("unauth/", views.unauth, name="unauth"),
    path("add_suborder/", views.add_suborder, name="add_suborder"),
    path("change_suborder/", views.change_suborder, name="change_suborder"),
    path("remove_suborder/", views.remove_suborder, name="remove_suborder"),
    path("submit_order/", views.submit_order, name="submit_order"),
    path("controlling/delete_billing", views.controlling_delete_billing, name="delete_billing"),
    path(
        "controlling/create_new_billing",
        views.controlling_create_new_billing,
        name="create_billing",
    ),
    path("get_suborders", views.my_orders_get_suborders, name="get_suborders"),
    path("change_state_of_order/", views.change_state_of_order, name="change_state_of_order"),
    path("save_staff_comment/", views.save_staff_comment, name="save_staff_comment"),
    path("messenger/save_message/", views.save_message, name="save_message"),
    path("get_orderstates_dict", views.get_orderstates_dict, name="get_orderstates_dict"),
    path("generate_preview", views.generate_preview, name="generate_preview"),
]
