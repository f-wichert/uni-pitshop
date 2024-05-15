import json
from datetime import datetime, timedelta
from typing import List, Mapping, Tuple

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, HttpRequest, HttpResponse
from django.http.response import HttpResponseForbidden, HttpResponseNotFound, HttpResponseRedirect
from django.shortcuts import redirect, render

from model.models import (
    Billing,
    BillingOrder,
    ExtendedUser,
    Material,
    MaterialVariation,
    Message,
    Order,
    OrderState,
    SubOrderLaserCut,
    SubOrderMaterial,
    WorkshopInformation,
)

# Use render_if_authenticated instead of render in most cases
# to make sure that unauthenticated users are always redirected to the login form


def render_if_authenticated(
    request: HttpRequest, template_name: str, context: Mapping[str, any] = None
) -> HttpResponse:
    """
    Render a template if the user is authenticated, otherwise redirect to the login form
    """
    if not request.user.is_authenticated:
        return HttpResponseRedirect("/login")
    return render(request, template_name, context=context)


def landing(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("client:produktauswahl")
    return redirect("client:login")


# Produktauswahl
@login_required
def produktauswahl_main_page(request: HttpRequest) -> HttpResponse:
    return render(request, "produktauswahl/produktauswahl_main_page.html")


@login_required
def produktauswahl_laserschnitt(request: HttpRequest) -> HttpResponse:
    material_data: List[Tuple[Material, str]] = []
    for mat in Material.objects.filter(variations__is_lasercutable=True).distinct():
        prices = set(v.price for v in mat.lasercutable_variations)
        # formats price as "ab <minimum>" if multiple different prices exist
        material_data.append(
            (mat, f"ab {min(prices)}" if len(prices) > 1 else str(list(prices)[0]))
        )

    return render(
        request,
        "produktauswahl/produktauswahl_laserschnitt.html",
        {"materials": material_data},
    )


@login_required
def produktauswahl_materialkauf(request: HttpRequest) -> HttpResponse:
    data = {
        "materials": [],
    }

    for material in Material.objects.all():
        variations = MaterialVariation.objects.all().filter(base=material)
        material.name = material.name.replace(" ", "_")

        data["materials"].append(
            {
                "object": material,
                "variations": variations,
            }
        )

    data["materials"] = Material.objects.all()

    return render(request, "produktauswahl/produktauswahl_materialkauf.html", data)


@login_required
def materialkauf_table(request: HttpRequest) -> HttpResponse:
    render_table_head = True
    render_type_column = False

    data = {
        "render_table_head": render_table_head,
        "render_type_column": render_type_column,
    }
    # TODO: This should render the table head if neccassary only,
    return render(request, "include/materialkauf/materialkauf_table.html", data)


@login_required
def cart_table(request: HttpRequest) -> HttpResponse:
    order = request.user.current_order
    context = {
        "order": order,
        "lasercuts": order.suborders_lasercuts if order else None,
        "materials": order.suborders_materials if order else None,
    }
    return render(request, "include/cart/cart_table.html", context)


@login_required
def cart_get_price(request: HttpRequest):
    if not (order := request.user.current_order):
        return HttpResponseNotFound()
    return HttpResponse(order.price_str)


@login_required
def get_lasercut_file(request: HttpRequest, lasercut_id: int) -> HttpResponse:
    try:
        lasercut: SubOrderLaserCut = SubOrderLaserCut.objects.get(id=lasercut_id)
    except Exception:
        return HttpResponseNotFound()

    user = request.user
    is_staff = user.is_staff

    if not (is_staff or lasercut.order.user == user):
        return HttpResponseForbidden()

    if not lasercut.file:
        return HttpResponseNotFound()

    filename = lasercut.filename_extended if is_staff else lasercut.filename

    response = HttpResponse(lasercut.file, content_type="application/octet-stream")
    response["Content-Disposition"] = f"attachment; filename={filename}"

    return response


# Login
def login(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("client:produktauswahl")
    return render(request, "login/login.html")


# Controlling
@staff_member_required
def controlling(request: HttpRequest) -> HttpResponse:
    return render(request, "controlling/controlling.html")


@staff_member_required
def controlling_filter(request: HttpRequest) -> HttpResponse:
    # only bill finished orders
    orders = Order.objects.filter(state=OrderState.FINISHED).exclude(is_rechnung=True)
    # Filtering Stuff
    if request.GET.get("idInput", "") != "":
        orders = orders.filter(id=request.GET.get("idInput"))
    if request.GET.get("nameInput", "") != "":
        orders = orders.filter(
            user__first_name__icontains=request.GET.get("nameInput")
        ) | orders.filter(user__last_name__icontains=request.GET.get("nameInput"))
    if request.GET.get("dateOrderedFromInput", "") != "":
        orders = orders.filter(date_ordered__gte=request.GET.get("dateOrderedFromInput"))
    if request.GET.get("dateOrderedUntilInput", "") != "":
        orders = orders.filter(date_ordered__gte=request.GET.get("dateOrderedFromInput"))
        # Need to add one day to make less than equal actually work (value is at 00:00 of day)
        dateUntilPlusOneDay = datetime.strptime(
            request.GET.get("dateOrderedFromInput"), "%Y-%m-%d"
        ) + timedelta(days=1)
        orders = orders.filter(date_ordered__lte=dateUntilPlusOneDay)
    if request.GET.get("billedInput", "") == "not-billed":
        orders = orders.exclude(billingorder__isnull=False)
    if request.GET.get("billedInput", "") == "billed":
        orders = orders.filter(billingorder__isnull=False)

    # reorder
    orderAmount = ""
    if request.GET.get("sort", "") != "":
        splitList = request.GET.get("sort").split(";")
        orderAmount = splitList[len(splitList) - 1]  # get orderAmountString
        del splitList[(len(splitList) - 1)]  # remove amount from order array
        sortArray = list(filter(lambda x: x != "", splitList))  # filter empty sorts
        if len(sortArray) == 0:  # default filter without involving the frontend
            orders = orders.order_by(
                "-id"
            )  # (better usability => user doesn't need to deselect id filter)
        else:
            orders = orders.order_by(*sortArray)

    # get price and reformat dates
    controlling_order_prep(orders)

    # Amount Filter
    orders = list(orders)
    indexToDeleteList = []
    if request.GET.get("amountFromInput") != "":
        min = float(request.GET.get("amountFromInput").replace(".", ","))
    else:
        min = 0
    if request.GET.get("amountUntilInput") != "":
        max = float(request.GET.get("amountUntilInput"))
    else:
        max = float("inf")
    for i, order in enumerate(orders):
        if order.price_float < min or order.price_float > max:
            indexToDeleteList.append(i)

    # remove filtered indexes from orders
    for i in reversed(indexToDeleteList):
        orders.pop(i)

    # order by price
    if orderAmount != "":
        orders.sort(key=lambda elem: elem.price_float, reverse="-" in orderAmount)

    return render(
        request,
        "include/controlling/entry.html",
        {
            "orders": orders,
        },
    )


@staff_member_required
def controlling_billing_modal(request: HttpRequest) -> HttpResponse:
    billings = Billing.objects.all().order_by("-date_billed")
    for billing in billings:
        orders = Order.objects.filter(billingorder__billing=billing.id).order_by("-date_ordered")
        billing.period = (
            orders[len(orders) - 1].date_ordered.strftime("%d.%m.%Y")
            + " - "
            + orders[0].date_ordered.strftime("%d.%m.%Y")
        )
    return render(
        request,
        "include/controlling/entry_alreadyBilled.html",
        {
            "billings": billings,
        },
    )


@staff_member_required
def controlling_print(request: HttpRequest) -> HttpResponse:
    billingId = request.GET.get("billingId")
    orders = Order.objects.filter(billingorder__billing=billingId).order_by("-id")
    wsinfo = get_workshop_information()
    return render(
        request,
        "include/controlling/entry_print.html",
        {
            "orders": orders,
            "wsinfo": wsinfo,
        },
    )


@staff_member_required
def controlling_automatic_billing_search(request: HttpRequest) -> HttpResponse:
    maxAmount = float(request.GET.get("maxAmount"))
    dateToBillFrom = request.GET.get("dateToBillFrom")
    # only get finished orders and exclude already billed orders

    orders = (
        Order.objects.filter(state=OrderState.FINISHED)
        .exclude(billingorder__isnull=False)
        .order_by("id")
    )
    orders = orders.filter(date_ordered__gte=dateToBillFrom)

    sum = 0
    indexToStop = len(orders)
    orders = list(orders)
    for i, order in enumerate(orders):
        if sum + order.price_float > maxAmount:
            indexToStop = i
            break
        sum += order.price_float
    orders = orders[:indexToStop]

    if len(orders) == 0:
        return HttpResponse("no_orders_found")

    # order_by('-id')
    orders = reversed(orders)

    return render(
        request,
        "include/controlling/entry_autoBilling.html",
        {
            "orders": orders,
        },
    )


# Helper Functions


def controlling_order_prep(orders):
    for order in orders:
        # If exists entry in BillingOrder with this object id it means it already has been billed
        billingOrder = BillingOrder.objects.filter(order_id=order.id)
        alreadyBilled = len(billingOrder) > 0
        # Add billed_date with specific string
        if not alreadyBilled:
            order.billed_date = "Noch nicht abgerechnet"
        else:
            billing = Billing.objects.get(id=billingOrder[0].billing_id)
            order.billed_date = (
                "Bereits abgerechnet (Datum: "
                + billing.date_billed.strftime("%d.%m.%Y")
                + " | ID: "
                + str(billing.id)
                + ")"
            )


# Customer Orders


def my_orders_entries(request: HttpRequest) -> HttpResponse:
    orders = Order.objects.all()
    orders = orders.filter(user=request.user).exclude(state=None)

    for order in orders:
        order.stateString = OrderState.as_dict[order.state]

        messages = Message.objects.filter(order=order.id)
        foundUnreadMessage = False
        for message in messages:
            if message.new_message and message.sender != order.user:
                foundUnreadMessage = True
        order.hasUnreadMessage = foundUnreadMessage

    return render_if_authenticated(
        request=request,
        template_name="include/my_orders/entry.html",
        context={
            "orders": orders,
        },
    )


def my_orders(request: HttpRequest, ID=None) -> HttpResponse:
    user = request.user
    data = {
        "user": user,
    }
    if ID is None:
        return render_if_authenticated(request=request, template_name="my_orders/my_orders.html")
    else:
        data["ID"] = ID
        data["render_table_head"] = True
        data["render_type_icon"] = False
        data["order"] = Order.objects.filter(id=ID).first()
        data["is_staff"] = False
        data["is_editable"] = True

        print(ID)
        return render(request=request, template_name="my_orders/my_order.html", context=data)


# Orders
@staff_member_required
def orders_overview(request: HttpRequest) -> HttpResponse:
    return render_if_authenticated(
        request, "orders/orders_overview.html", {"orderStates": OrderState.as_dict}
    )


# Return all orders matching a filter criterion
def filtered_orders(request: HttpRequest) -> HttpResponse:

    if not request.user.is_staff:
        return HttpResponse("get_filtered_orders: You are not allowed to view this page")

    # Get the filter Values
    filterValues: dict[str, str] = json.loads(request.body)

    # Get all orders
    orders = Order.objects.all()

    # Get Order States
    orderStates = OrderState.as_dict

    # Exclude orders that do not have a state / have not been submitted
    orders = orders.exclude(state=None)

    # Helper function to check if filterValues is a valid filter
    def isValidFilter(filter: str) -> bool:
        return not len(filterValues[filter]) == 0

    if isValidFilter("status"):
        orders = orders.filter(state__in=filterValues["status"])

    if isValidFilter("dateFrom"):
        orders = orders.filter(
            date_ordered__gte=datetime.strptime((filterValues["dateFrom"]), "%Y-%m-%d")
        )

    if isValidFilter("dateUntil"):
        orders = orders.filter(
            date_ordered__gte=datetime.strptime((filterValues["dateUntil"]), "%Y-%m-%d")
        )

    if isValidFilter("id"):
        orders = orders.filter(id=filterValues["id"])

    if isValidFilter("name"):
        orders = (
            orders.filter(user__first_name__iregex=filterValues["name"])
            | orders.filter(user__last_name__iregex=filterValues["name"])
            | orders.filter(user__matr_nr__iregex=filterValues["name"])
        )

    for order in orders:
        order.stateString = orderStates[order.state]

        messages = Message.objects.filter(order=order.id)
        foundUnreadMessage = False
        for message in messages:
            if message.new_message and message.sender == order.user:
                foundUnreadMessage = True
        order.hasUnreadMessage = foundUnreadMessage

    return render(
        request,
        "include/orders/order_row.html",
        {
            "orders": orders,
            "orderStates": orderStates,
            "is_staff": True,
            "is_editable": True,
        },
    )


@staff_member_required
def orders_quittung(request: HttpRequest) -> HttpResponse:
    order = Order.objects.get(id=int(request.GET.get("orderId")))

    wsinfo = get_workshop_information()

    if request.GET.get("alternateDate"):
        order.date_ordered = datetime.strptime(
            request.GET.get("alternateDate"), "%Y-%m-%d"
        ).strftime("%d.%m.%Y")
    else:
        order.date_ordered = order.date_ordered.strftime("%d.%m.%Y")
    # TODO: Add new Service
    purposeArray = []
    allSubOrders = order.suborders
    if len([order for order in allSubOrders if isinstance(order, SubOrderLaserCut)]) > 0:
        purposeArray.append("Laserarbeiten")
    if len([order for order in allSubOrders if isinstance(order, SubOrderMaterial)]) > 0:
        purposeArray.append("Materialkauf")
    # if len([order for order in allSubOrders if isinstance(order, SubOrder3dPrint)]) > 0:
    #     purposeArray.append("3D-Druck")

    purposeString = "Für "

    if len(purposeArray) == 1:
        purposeString += purposeArray[0]
    if len(purposeArray) == 2:
        purposeString += purposeArray[0] + " und " + purposeArray[1]
    if len(purposeArray) >= 3:
        for i, purpose in enumerate(purposeArray):
            if i == len(purposeArray) - 1:
                purposeString += " und " + purpose
            elif i == len(purposeArray) - 2:
                purposeString += purpose
            else:
                purposeString += purpose + ", "

    order.purposeString = purposeString
    return render(
        request,
        "include/orders/quittung.html",
        {
            "order": order,
            "wsinfo": wsinfo,
        },
    )


def orders_invoice_data(request: HttpRequest) -> HttpResponse:
    order = Order.objects.get(id=int(request.GET.get("orderId")))

    return render(
        request,
        "include/orders/payment_data.html",
        {
            "order": order,
        },
    )


def orders_invoice(request: HttpRequest) -> HttpResponse:
    invoiceInfo = {
        "invoiceNr": request.GET.get("invoiceNr"),
        "invoiceDate": datetime.strptime(request.GET.get("invoiceDate"), "%Y-%m-%d").strftime(
            "%d.%m.%Y"
        ),
        "invoiceAdress": request.GET.get("invoiceAdress"),
        "invoiceIntro": request.GET.get("invoiceIntro"),
    }

    wsinfo = get_workshop_information()

    services = json.loads(request.GET.get("serviceArray"))
    totalAmount = 0
    for service in services:
        totalAmount += float(service["total_price"])
        service["price"] = float_to_price(float(service["price"]))
        service["total_price"] = float_to_price(float(service["total_price"]))

    mwst = float(wsinfo["MwSt"]) / 100
    totalAmountGross = float_to_price(totalAmount * (1.0 + mwst))
    taxes = float_to_price(totalAmount * mwst)
    totalAmount = float_to_price(totalAmount)

    return render(
        request,
        "include/orders/invoice.html",
        {
            "invoiceInfo": invoiceInfo,
            "services": services,
            "totalAmount": totalAmount,
            "taxes": taxes,
            "totalAmountGross": totalAmountGross,
            "wsinfo": wsinfo,
        },
    )


def orders_material_data_for_lasercut(request: HttpRequest) -> HttpResponse:
    print(request.GET)
    order = Order.objects.get(id=int(request.GET.get("orderId")))

    if order.user != request.user and not request.user.is_staff:
        return HttpResponseForbidden()
    lasercut_suborder = SubOrderLaserCut.objects.get(id=int(request.GET.get("suborderId")))
    material_suborders = SubOrderMaterial.objects.all().filter(
        associated_lasercut=lasercut_suborder
    )

    return render(
        request,
        "include/orders/suborder_row_lasercut_materiallist.html",
        {
            "order": order,
            "lasercut_suborder": lasercut_suborder,
            "material_suborders": material_suborders,
            "is_staff": True,
            "is_editable": True,
        },
    )


def float_to_price(price):
    return "{:.2f}".format(price).replace(".", ",")


def get_workshop_information():
    wsinfos = WorkshopInformation.objects.all()
    wsinfosDict = {wsinfo.descriptor: wsinfo.value for wsinfo in wsinfos}
    return wsinfosDict


def orders_quittung_data(request: HttpRequest) -> HttpResponse:
    order = Order.objects.get(id=int(request.GET.get("orderId")))

    return render(
        request,
        "include/orders/quittung_data.html",
        {
            "order": order,
        },
    )


def orders_payment_state(request: HttpRequest) -> HttpResponse:
    orderId = int(request.GET.get("orderId"))
    isRechnung = json.loads(request.GET.get("isRechnung"))
    order = Order.objects.get(id=orderId)
    order.is_rechnung = isRechnung
    order.save()
    return HttpResponse("Succesfully updated order state")


# Messenger
def get_messages(request: HttpRequest) -> HttpResponse:
    order = Order.objects.get(id=int(request.GET.get("orderId")))
    user = ExtendedUser.objects.get(username=request.user)
    messages = Message.objects.filter(order=order.id)

    # user is not allowed to send requests for orders that aren't his
    if not user.is_staff and order.user != user:
        return HttpResponseRedirect("/produktauswahl")

    for message in messages:
        if message.sender != order.user:
            message.recipient = True
        else:
            message.recipient = False
            if message.new_message:
                message.new_message = False
                message.save()

    return render(
        request,
        "include/messenger/message.html",
        {
            "messages": messages,
        },
    )


def get_messages_user(request: HttpRequest) -> HttpResponse:
    order = Order.objects.get(id=int(request.GET.get("orderId")))
    user = ExtendedUser.objects.get(username=request.user)
    messages = Message.objects.filter(order=order.id)

    # user is not allowed to send requests for orders that aren't his
    if not user.is_staff and order.user != user:
        return HttpResponseRedirect("/produktauswahl")

    for message in messages:
        if message.sender != order.user:
            message.recipient = False
            if message.new_message:
                message.new_message = False
                message.save()
        else:
            message.recipient = True

    return render(
        request,
        "include/messenger/message.html",
        {
            "messages": messages,
        },
    )


def preview_images(request: HttpRequest, img=None) -> HttpResponse:
    if img is None:
        return HttpResponse("No image given!")
    else:
        img = open(f"media/preview_images/{img}", "rb")

        response = FileResponse(img)

        return response
