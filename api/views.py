import json
import sys
from json import loads
from typing import Any, Dict, List, Tuple, Union
from urllib.parse import urljoin

import requests
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from django.http import FileResponse, HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from django.utils import timezone

from model.models import (
    Billing,
    BillingOrder,
    ExtendedUser,
    MaterialVariation,
    Message,
    Order,
    OrderState,
    SubOrder,
    SubOrderLaserCut,
    SubOrderMaterial,
)

# Login API calls


def auth(request: HttpRequest) -> HttpResponse:
    """
    Authenticates a user with the given HttpRequest.
    The request has to have the data type JSON and must follow these conditons

    {
        username: sample_user,
        password: sample_password,i
    }
    """
    data = json.loads(request.body)
    username = data["username"]
    password = data["password"]

    user = authenticate(request, username=username, password=password)

    if user is None or not user.is_active:
        return HttpResponse("auth:false")

    login(request, user)

    return HttpResponse("auth:true")


def unauth(request: HttpRequest) -> HttpResponse:
    """
    Unauthenticate the currently logged-in user
    """
    if not request.user.is_authenticated:
        print("unauth: user is not authenticated", file=sys.stderr)
        return HttpResponse("unauth:false")

    logout(request)

    return HttpResponse("unauth:true")


# Shopping cart API


def add_suborder(request: HttpRequest) -> HttpResponse:
    """
    Add a suborder to the users current order.
    If the user doesn't have an order, create one.

    Order format

    {
        type: 'lasercut' | 'material'
        comment: str

        [case laser]
        file: blob?

        [case material]
        amount: 0 < int < 100
        material_name: str
        variation_id: int
        width:  int [mm]
        length: int [mm]
    }
    """
    if not isinstance(request.user, ExtendedUser):
        print("add_suborder: user is not a valid ExtendedUser", file=sys.stderr)
        return HttpResponse("add_suborder:false")

    data: Dict[str, Any] = {}
    if request.content_type == "multipart/form-data":
        type_of_order = request.POST["type"]
    else:
        # TODO: use multipart for all requests
        data = json.loads(request.body)
        type_of_order = data["type"]

    if "order_id" in data and request.user.is_staff:
        order = Order.objects.get(id=int(data["order_id"]))
    else:
        order = request.user.get_or_create_current_order()

    success = False

    if type_of_order == "lasercut":
        print("LASERCUT")
        success = add_laser_cut_order(request, order)
    elif type_of_order == "material":
        success = add_material_order(data, order)
    else:
        print(f"add_suborder: encountered invalid {type_of_order = }", file=sys.stderr)

    return HttpResponse(f"add_suborder:{str(success).lower()}")


def add_laser_cut_order(req: HttpRequest, order: Order) -> bool:
    # TODO: limit file size
    if not (file := req.FILES.get("upload-file")):
        print("add_laser_cut_order: no file uploaded", file=sys.stderr)
        return False

    data = req.POST
    try:
        material_variations = list(map(int, data.getlist("lc-variation")))
        material_cuts = [
            (int(a), int(b))
            for a, b in zip(data.getlist("lc-cut-length"), data.getlist("lc-cut-width"))
        ]
        counts = list(map(int, data.getlist("lc-count")))
        assert len(material_variations) == len(material_cuts) == len(counts)
    except Exception as e:
        print("add_laser_cut_order: incorrect order format: ", e, file=sys.stderr)
        return False

    jobs: List[Tuple[MaterialVariation, Tuple[int, int], int]] = []
    for variation_id, cut, count in zip(material_variations, material_cuts, counts):
        jobs.append((MaterialVariation.objects.get(id=variation_id), cut, count))

    comment: str = data["comment"]

    # TODO: check all values for correctness
    if len(comment) > 10000:
        return False

    with transaction.atomic():
        s = SubOrderLaserCut.objects.create(
            order=order,
            customer_comment=comment,
            file=file,
        )

        # NOTE: not using bulk_create as it has a number of caveats that make things difficult
        for variation, cut, count in jobs:
            is_fixed = variation.base.is_fixed_size
            # TODO: duplicate reference to order (see above)
            s.parts.create(
                order=order,
                material=variation,
                amount=count,
                size_length=None if is_fixed else cut[0],
                size_width=None if is_fixed else cut[1],
            )

    return True


def add_material_order(data: dict[str, Any], order: Order) -> bool:
    s = SubOrderMaterial()
    print(data)
    try:
        s.order = order
        s.amount = int(data["amount"])
        s.material = MaterialVariation.objects.get(id=int(data["variation_id"]))
        if "comment" in data:
            s.comment = data["comment"]
        if "width" in data:
            s.size_width = int(data["width"])
        if "length" in data:
            s.size_length = int(data["length"])
        if "lasercut_id" in data:
            s.associated_lasercut = SubOrderLaserCut.objects.get(id=int(data["lasercut_id"]))
    except Exception as e:
        print("add_material_order: encountered incorrect order format: ", e, file=sys.stderr)
        return False

    # TODO: check all values for correctness properly
    if (s.amount > 99 or len(s.comment) > 10000 or s.material is None) or (
        not s.material.is_fixed
        and (
            s.size_width < 1
            or s.size_width > s.material.width
            or s.size_length < 1
            or s.size_length > s.material.length
        )
    ):
        print("One of the statement was false...")
        return False

    s.save()

    return True


def change_suborder(request: HttpRequest) -> HttpResponse:
    """
    Change the suborder with the given type and id from the current users order
    or from the order with `order_id` if it is specified

    The possible changes that can be made depend on the type of the suborder.
    Everything except type and id is optional

    {
        order_id: int

        type: 'lasercut' | 'material'
        id: int

        newState: bool

        comment: str

        price: int

        reset_price_override: bool

        [case lasercut]
        minutes: int

        [case material]
        amount: int
        length: int
        width: int
        height: int
        variation_id: int

        get_price: bool
        get_price_str: bool
        get_order_price: bool
        get_order_price_str: bool
    }
    """
    if not isinstance(request.user, ExtendedUser):
        print("change_suborder: user is not a valid ExtendedUser", file=sys.stderr)
        return JsonResponse(
            {
                "change_suborder": False,
            }
        )

    data: dict[str, Any] = json.loads(request.body)
    suborder_type: str = data["type"]
    suborder_id: int = data["id"]

    print(data)

    if "order_id" in data:
        order = Order.objects.get(pk=data["order_id"])
        if not request.user.is_staff:
            print("change_suborder: only staff can specify order_id", file=sys.stderr)
            return JsonResponse(
                {
                    "change_suborder": False,
                }
            )
    else:
        order = request.user.current_order

    if order is None:
        print("change_suborder: order is None")
        return JsonResponse(
            {
                "change_suborder": False,
            }
        )

    suborder = SubOrder.get_suborder_by_type(suborder_type, order=order, id=suborder_id)

    if suborder is None:
        print(
            f"change_suborder: user doesnt have {suborder_type} suborder with {suborder_id = }",
            file=sys.stderr,
        )
        return JsonResponse(
            {
                "change_suborder": False,
            }
        )

    if "newState" in data:
        suborder.is_completed = data["newState"]  # Added
    if "comment" in data:
        suborder.customer_comment = data["comment"]  # Added
    if "reset_price_override" in data:
        suborder.price_override = None
    if "price" in data:
        suborder.price_override = int(data["price"])

    if isinstance(suborder, SubOrderMaterial):
        if "variation_id" in data:
            suborder.material = MaterialVariation.objects.get(id=data["variation_id"])

        if "amount" in data and (0 < (amount := int(data["amount"])) < 100):
            suborder.amount = amount

        if "height" in data:
            height = int(data["height"])
            mat_length = suborder.material.length
            is_fixed = suborder.material.is_fixed
            if (not is_fixed and 0 < height <= mat_length) or (is_fixed and height == mat_length):
                suborder.size_length = height

        if "length" in data:
            length = int(data["length"])
            mat_length = suborder.material.length
            is_fixed = suborder.material.is_fixed
            if (not is_fixed and 0 < length <= mat_length) or (is_fixed and length == mat_length):
                suborder.size_length = length

        if "width" in data:
            width = int(data["width"])
            mat_width = suborder.material.width
            is_fixed = suborder.material.is_fixed
            if (not is_fixed and 0 < width <= mat_width) or (is_fixed and width == mat_width):
                suborder.size_width = width

    if isinstance(suborder, SubOrderLaserCut):
        if "minutes" in data:
            suborder.minutes = int(data["minutes"])

    suborder.save()

    response_data = {
        "change_suborder": True,
    }

    if "get_price" in data and data["get_price"]:
        response_data["price"] = suborder.price

    if "get_price_str" in data and data["get_price_str"]:
        response_data["price_str"] = suborder.price_str

    if "get_order_price" in data and data["get_order_price"]:
        response_data["order_price"] = suborder.order.price

    if "get_order_price_str" in data and data["get_order_price_str"]:
        response_data["order_price_str"] = suborder.order.price_str

    return JsonResponse(response_data)


def remove_suborder(request: HttpRequest) -> HttpResponse:
    """
    Remove the suborder with the given type and id from the current users order
    or from the order with `order_id` if it is specified

    {
        type: 'lasercut' | 'material'
        id: int

        order_id: int
    }
    """
    if not isinstance(request.user, ExtendedUser):
        print("remove_suborder: user is not a valid ExtendedUser", file=sys.stderr)
        return HttpResponse("remove_suborder:false")

    data: dict[str, Any] = json.loads(request.body)
    suborder_type: str = data["type"]
    suborder_id: int = data["id"]

    if "order_id" in data:
        if not request.user.is_staff:
            print("remove_suborder: only staff can specify order_id", file=sys.stderr)
            return HttpResponse("remove_suborder:false")
        order = Order.objects.get(pk=data["order_id"])
    else:
        order = request.user.current_order

    if order is None:
        print("remove_suborder: order is None")
        return HttpResponse("remove_suborder:false")

    suborder = SubOrder.get_suborder_by_type(suborder_type, order=order, id=suborder_id)

    if suborder is None:
        print(f"remove_suborder: user doesnt have suborder with {suborder_id = }", file=sys.stderr)
        return HttpResponse("remove_suborder:false")

    suborder.delete()

    if len(order.suborders) == 0:
        order.delete()

    print("remove_suborder:true")

    return HttpResponse("remove_suborder:true")


def submit_order(request: HttpRequest) -> HttpResponse:
    if not isinstance(request.user, ExtendedUser):
        print("submit_order: user is not a valid ExtendedUser", file=sys.stderr)
        return HttpResponse("submit_order:false")

    if request.user.has_unfinished_order:
        print(
            "submit_order: a user tried to submit an order, even though they have an unpaid order",
            file=sys.stderr,
        )
        return HttpResponse("submit_order:unpaid_order")

    order = request.user.current_order

    if order is None:
        print("submit_order: a user tried to submit a non-existent order", file=sys.stderr)
        return HttpResponse("submit_order:false")

    order.state = OrderState.SUBMITTED
    order.save()
    return HttpResponse("submit_order:true")


# Controlling
def controlling_delete_billing(request: HttpRequest) -> HttpResponse:
    # Don't send response if user is not staff
    if not request.user.is_staff:
        return HttpResponseRedirect("/produktauswahl")

    id = loads(request.body).get("billingIdToDelete")

    billing = Billing.objects.get(id=id)

    # set billed_price of all suborders of orders to null
    for billingorder in billing.get_all_billing_orders:
        billingorder.order.state = OrderState.FINISHED
        billingorder.order.save()
        for suborder in billingorder.order.suborders:
            suborder.price_billed = None
            suborder.save()

    # BillingOrder also gets cleaned up because of cascade on foreign keys
    billing.delete()
    return HttpResponse("Billing was deleted successfully.")


def controlling_create_new_billing(request: HttpRequest) -> HttpResponse:
    # Don't send response if user is not staff
    if not request.user.is_staff:
        return HttpResponseRedirect("/produktauswahl")

    idString = loads(request.body).get("orderIdsToBill")
    if idString != "":
        controlling_create_new_billing_backend(idString, request.user)
    return HttpResponse("New billing was created successfully.")


def controlling_create_new_billing_backend(idString, user):
    # Insert new Billing and add BillingOrder assignments for each OrderId
    orderIdArray = list(filter(lambda x: x != "", idString.split(";")))
    user_id = ExtendedUser.objects.get(username=user).id
    billing = Billing(user_id=user_id, date_billed=timezone.now())
    billing.save()
    for orderId in orderIdArray:
        order = Order.objects.get(id=orderId)
        BillingOrder(billing=billing, order=order).save()
        order.state = OrderState.BILLED
        order.save()
        for suborder in order.suborders:
            if suborder.price_override:
                suborder.price_billed = suborder.price_override
            else:
                suborder.price_billed = suborder.price
            suborder.save()


def my_orders_get_suborders(request: HttpRequest) -> HttpResponse:
    if not isinstance(request.user, ExtendedUser):
        print("my_orders_get_orders: user is not a valid ExtendedUser", file=sys.stderr)
        return HttpResponse("my_orders_get_orders:false")

    ID = loads(request.body).get("ID")
    print("Gebe ID zurück:", ID)

    order = Order.objects.get(id=ID)

    print("Gebe Order zurück:", order.__dict__)
    if order is None:
        print("my_orders_get_orders: order is None", file=sys.stderr)
        return HttpResponse("my_orders_get_orders:false")

    lasercutSuborders = order.suborders_lasercuts
    materialSuborders = order.suborders_materials

    lasercutResponse = []

    for suborder in lasercutSuborders:
        lasercutResponse.append(
            {
                "id": suborder.id,
                "material": suborder.material.name,
                "is_completed": suborder.is_completed,
                "price-estimate": suborder.price,
                "date": order.date_ordered.strftime("%d.%m.%Y %H:%M:%S"),
                "comment": suborder.customer_comment,
            }
        )

    materialResponse = []

    for suborder in materialSuborders:
        materialResponse.append(
            {
                "id": suborder.id,
                "material": suborder.material.name,
                "is_completed": suborder.is_completed,
                "price": suborder.price,
                "date": order.date_ordered.strftime("%d.%m.%Y %H:%M:%S"),
                "size_width": suborder.size_width,
                "size_height": suborder.size_length,
                "quantity": suborder.amount,
                "comment": suborder.customer_comment,
            }
        )

    return JsonResponse([lasercutResponse, materialResponse], safe=False)


def change_state_of_order(request: HttpRequest) -> HttpResponse:
    if not request.user.is_staff:
        return HttpResponse("change_state_of_order:false")
    body = loads(request.body)
    orderId = int(body.get("orderId"))
    newState = int(body.get("newState"))

    order = Order.objects.get(id=orderId)
    order.state = newState
    order.save()

    return HttpResponse("change_state_of_order:true")


def save_staff_comment(request: HttpRequest) -> HttpResponse:
    if not request.user.is_staff:
        return HttpResponse("change_state_of_order:false")
    body = loads(request.body)
    orderId = int(body.get("orderId"))
    print(body)
    staff_comment = body.get("staffComment")

    order = Order.objects.get(id=orderId)
    order.staff_comment = staff_comment
    order.save()

    return HttpResponse("staff_comment change successful")


def get_orderstates_dict(request: HttpRequest) -> JsonResponse:
    if request.user.is_authenticated:
        return JsonResponse(OrderState.as_dict, safe=False)


# Message Application
def save_message(request: HttpRequest) -> HttpResponse:
    order = Order.objects.get(id=int(loads(request.body).get("orderId")))
    message = loads(request.body).get("message")
    sender = ExtendedUser.objects.get(username=request.user)

    # To prevent users from creating messages for orders other than their own by sending requests
    if sender == order.user or request.user.is_staff:
        Message(order=order, sender=sender, text=message).save()
        return HttpResponse("New billing was created successfully.")
    return HttpResponse("You're not allowed to save this message.")


def generate_preview(request: HttpRequest) -> Union[HttpResponse, FileResponse]:
    if not request.user.is_authenticated:
        return HttpResponse(status=403)

    if not (file := request.FILES.get("upload-file")):
        print("generate_preview: no file uploaded", file=sys.stderr)
        return HttpResponse(status=418)

    if file.size > 10 * 1024 * 1024:
        print(f"generate_preview: file too large ({file.size} bytes)", file=sys.stderr)
        return HttpResponse(status=418)

    with file.open("rb") as f:
        res = requests.post(
            urljoin(settings.LASERCUT_PREVIEW_ENDPOINT, "render"), files={"file": f}, stream=True
        )
    res.raise_for_status()

    return FileResponse(res.raw, content_type=res.headers.get("content-type", None))
