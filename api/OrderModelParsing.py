# This file contains functionallity to parse an order from Django.models to the client-side format.
# It also adds information about the suborders needed for the Orderoverview.

from typing import Any, Dict, Union

from django.db.models import QuerySet

# import _strptime
from model.models import Order, SubOrderLaserCut, SubOrderMaterial


# Takes list of Orders and adds all necessary information for displaying the orderoverview
def parse_orders(orders: Union[QuerySet, Dict[str, Any]]) -> list[dict]:
    print("Orders$$$$: ", orders, "End of orders")
    parsed_orders = []
    for order in orders:
        parsed_orders.append(parse_order(order))
    return parsed_orders


def parse_order(order: Order) -> dict:
    parsed_order = {}
    parsed_order["id"] = order.id
    parsed_order["name"] = (
        order.user.first_name + " " + order.user.last_name + " (" + str(order.user.matr_nr) + ")"
    )
    parsed_order["date"] = order.date_ordered
    parsed_order["status"] = order.state
    parsed_order["staffComment"] = order.staff_comment

    # Get all Lasercut and Material suborders
    allOrders = order.suborders
    lasercutOrders = [order for order in allOrders if isinstance(order, SubOrderLaserCut)]
    materialOrders = [order for order in allOrders if isinstance(order, SubOrderMaterial)]

    parsed_order["lasercutSuborders"] = parse_lasercutSuborders(lasercutOrders)
    parsed_order["materialSuborders"] = parse_materialSuborders(materialOrders)
    return parsed_order


def parse_lasercutSuborders(suborders: list[SubOrderLaserCut]) -> list[dict]:
    parsed_suborders = []
    for suborder in suborders:
        parsed_suborders.append(parse_lasercutSuborder(suborder))
    return parsed_suborders


def parse_lasercutSuborder(suborder: SubOrderLaserCut) -> dict:
    parsed_suborder = {}
    parsed_suborder["id"] = suborder.id
    parsed_suborder["idOfParent"] = suborder.order.id
    parsed_suborder["filename"] = suborder.filename
    parsed_suborder["isCompleted"] = suborder.is_completed
    parsed_suborder["comment"] = suborder.customer_comment
    parsed_suborder["price"] = suborder.price
    parsed_suborder["pricePerMinute"] = suborder.price_per_minute
    return parsed_suborder


def parse_materialSuborders(suborders: list[SubOrderMaterial]) -> list[dict]:
    parsed_suborders = []
    for suborder in suborders:
        parsed_suborders.append(parse_materialSuborder(suborder))
    return parsed_suborders


def parse_materialSuborder(suborder: SubOrderMaterial) -> dict:
    parsed_suborder = {}
    parsed_suborder["id"] = suborder.id
    parsed_suborder["idOfParent"] = suborder.order.id

    parsed_suborder["material"] = suborder.material.name
    parsed_suborder["quantity"] = suborder.amount
    parsed_suborder["size_width"] = suborder.size_width
    parsed_suborder["size_height"] = suborder.size_height
    parsed_suborder["isCompleted"] = suborder.is_completed
    parsed_suborder["comment"] = suborder.customer_comment
    parsed_suborder["price"] = suborder.price
    return parsed_suborder
