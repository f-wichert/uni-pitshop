import math
import os
from typing import TYPE_CHECKING, Any, Dict, Optional, Type, cast

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.dispatch import receiver
from django.utils import timezone


class CustomBaseModel(models.Model):
    class Meta:
        abstract = True

    # run full clean on save, which runs validators (etc.)
    # forms already run full_clean and generally provide better UX, but we're not using forms
    def save(self, *args: Any, **kwargs: Any) -> None:
        self.full_clean()
        super().save(*args, **kwargs)


class ExtendedUserRole(models.IntegerChoices):
    INTERNAL_STUDENT = 0
    EXTERNAL_STUDENT = 1
    EXTERNAL_CUSTOMER = 2


class ExtendedUser(AbstractUser):
    tu_id = models.CharField("TU-ID", max_length=10, null=True, blank=True)
    matr_nr = models.IntegerField("Matriculation number", null=True, blank=True)
    role = models.IntegerField(
        "Role", choices=ExtendedUserRole.choices, default=ExtendedUserRole.EXTERNAL_STUDENT
    )

    @property
    def current_order(self) -> Optional["Order"]:
        try:
            return Order.objects.get(user=self, state=None)
        except Order.DoesNotExist:
            return None

    @property
    def has_unfinished_order(self) -> bool:
        return (
            Order.objects.filter(user=self)
            .exclude(state=OrderState.FINISHED)
            .exclude(state=None)
            .exists()
        )

    def get_or_create_current_order(self) -> "Order":
        """get the users current order, if they don't have one, create one"""
        order = self.current_order
        if order is None:
            order = Order(user=self)
            order.save()
        return order


class Material(CustomBaseModel):
    # make pylance shut up
    if TYPE_CHECKING:
        variations: models.QuerySet["MaterialVariation"]

    name = models.CharField(max_length=100)
    default_length = models.IntegerField()
    default_width = models.IntegerField()
    is_fixed_size = models.BooleanField()
    is_material_available = models.BooleanField(default=True)
    needs_comment = models.BooleanField(default=False)
    material_tooltip = models.TextField(blank=True, default="")
    previewImage = models.ImageField(null=True, blank=True, upload_to="preview_images/")

    @property
    def spaceless_name(self) -> str:
        return self.name.replace(" ", "_")

    @property
    def distinct_thicknesses(self) -> list["MaterialVariation"]:
        thick_set: set[float] = set()
        variations: list[MaterialVariation] = []
        for v in self.variations.all():
            if v.thickness not in thick_set:
                thick_set.add(v.thickness)
                variations.append(v)
        return variations

    @property
    def dimension_variations(self) -> list["MaterialVariation"]:
        # TODO: maybe remake this with distinct when we change over to Postgres
        dim_set: set[tuple[int, int]] = set()
        variations: list[MaterialVariation] = []
        for v in self.variations.all():
            if (v.width, v.length) not in dim_set:
                dim_set.add((v.width, v.length))
                variations.append(v)
        return variations

    @property
    def lasercutable_variations(self) -> models.QuerySet["MaterialVariation"]:
        return self.variations.filter(is_lasercutable=True)

    @property
    def has_lasercutable_variation(self) -> bool:
        return self.lasercutable_variations.exists()

    @property
    def variation(self) -> Optional["MaterialVariation"]:
        return self.variations.first()

    def __str__(self) -> str:
        return self.name


class MaterialVariation(CustomBaseModel):
    base = models.ForeignKey(Material, on_delete=models.CASCADE, related_name="variations")
    # TODO: this probably shouldn't be a float
    thickness = models.FloatField()
    price = models.IntegerField()
    non_default_length = models.IntegerField(null=True, blank=True)
    non_default_width = models.IntegerField(null=True, blank=True)
    is_lasercutable = models.BooleanField()
    is_variation_available = models.BooleanField(default=True)

    @property
    def name(self) -> str:
        return self.base.name

    @property
    def length(self) -> int:
        ndl = self.non_default_length
        return ndl if ndl else self.base.default_length

    @property
    def width(self) -> int:
        ndw = self.non_default_width
        return ndw if ndw else self.base.default_width

    @property
    def is_available(self) -> bool:
        return self.is_variation_available and self.base.is_material_available

    @property
    def is_fixed(self) -> bool:
        return self.base.is_fixed_size

    @property
    def needs_comment(self) -> bool:
        return self.base.needs_comment

    @property
    def material_tooltip(self) -> Optional[str]:
        return self.base.material_tooltip

    @property
    def thickness_variations(self) -> models.QuerySet["MaterialVariation"]:
        return MaterialVariation.objects.filter(
            base=self.base,
            non_default_width=self.non_default_width,
            non_default_length=self.non_default_length,
        )

    @property
    def dimension_variations(self) -> models.QuerySet["MaterialVariation"]:
        return MaterialVariation.objects.filter(
            base=self.base,
            thickness=self.thickness,
        )

    @property
    def has_more_than_one_dimension_variation(self) -> bool:
        return self.dimension_variations.count() > 1

    def __str__(self) -> str:
        return f"{self.base.name}: {self.thickness}mm"


class OrderState(models.IntegerChoices):
    SUBMITTED = 0
    IN_PROGRESS = 1
    AWAITING_REPLY = 2
    READY_FOR_PICKUP = 3
    FINISHED = 4
    BILLED = 5

    @classmethod
    @property
    def as_dict(self) -> Dict[int, str]:
        return {
            OrderState.SUBMITTED: "Neu",
            OrderState.IN_PROGRESS: "In Bearbeitung",
            OrderState.AWAITING_REPLY: "Warten auf Rückmeldung",
            OrderState.READY_FOR_PICKUP: "Abholbereit",
            OrderState.FINISHED: "Abgeschlossen",
            OrderState.BILLED: "Abgerechnet",
        }


class Order(CustomBaseModel):
    user = models.ForeignKey(ExtendedUser, on_delete=models.RESTRICT)
    date_ordered = models.DateTimeField(default=timezone.now)
    state = models.IntegerField(choices=OrderState.choices, default=None, blank=True, null=True)
    staff_comment = models.TextField(blank=True, default="")
    is_rechnung = models.BooleanField(default=False)

    @property
    def suborders_lasercuts(self) -> list["SubOrderLaserCut"]:
        return list(self.suborderlasercut_set.all())

    @property
    def has_lasercut_suborder(self) -> bool:
        return len(self.suborders_lasercuts) > 0

    @property
    def suborders_materials(self) -> list["SubOrderMaterial"]:
        return list(self.subordermaterial_set.all())

    @property
    def has_material_suborder(self) -> bool:
        return len(self.suborders_materials) > 0

    @property
    def suborders(self) -> list["SubOrder"]:
        return [*self.suborders_lasercuts, *self.suborders_materials]

    @property
    def are_all_suborders_completed(self) -> bool:
        for suborder in self.suborders:
            if not suborder.is_completed and not (
                isinstance(suborder, SubOrderMaterial) and suborder.associated_lasercut
            ):
                return False
        return True

    @property
    def is_finished(self) -> bool:
        return (
            self.state == OrderState.READY_FOR_PICKUP
            or self.state == OrderState.FINISHED
            or self.state == OrderState.BILLED
        )

    @property
    def price(self) -> int:
        """Returns the price of the order in cents"""
        return sum(suborder.price for suborder in self.suborders)

    @property
    def price_str(self) -> str:
        """Returns a `str` representation of the price of the order in euro"""
        return f"{(self.price / 100.0):.2f}".replace(".", ",")

    @property
    def price_float(self) -> float:
        """Returns the price of the order in euro"""
        return self.price / 100.0


class SubOrder(CustomBaseModel):
    class Meta:
        abstract = True

    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    price_override = models.IntegerField(null=True, blank=True)
    price_billed = models.IntegerField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    customer_comment = models.TextField(blank=True, default="")

    @property
    def price(self) -> int:
        raise Exception("SubOrder cannot be instantiated and has no price")

    @property
    def price_str(self) -> str:
        """Returns a `str` representation of the price of the suborder in euro"""
        return f"{(self.price / 100.0):.2f}".replace(".", ",")

    @property
    def price_float(self) -> float:
        return self.price / 100.0

    @property
    def price_valuestr(self) -> str:
        return f"{(self.price / 100.0):.2f}"

    @staticmethod
    def get_suborder_by_type(typ: str, *args: Any, **kwargs: Any) -> Optional["SubOrder"]:
        suborder: Optional["SubOrder"] = None

        try:
            if typ == "lasercut":
                suborder = SubOrderLaserCut.objects.get(*args, **kwargs)
            elif typ == "material":
                suborder = SubOrderMaterial.objects.get(*args, **kwargs)
            else:
                print(f"get_suborder_by_type: encountered invalid {typ = }")
        except Exception:
            print("get_suborder_by_type: suborder does not exist:", kwargs)

        return suborder


class LasercutMinutePrice(CustomBaseModel):
    role = models.IntegerField(choices=ExtendedUserRole.choices)
    price_per_minute = models.IntegerField()


def lasercut_file_location(instance: "SubOrderLaserCut", filename: str) -> str:
    return f"uploads/user_{instance.order.user.id}/order_{instance.order.id}/{filename}"


class SubOrderLaserCut(SubOrder):
    file = models.FileField(upload_to=lasercut_file_location, null=True, blank=True)
    upload_date = models.DateTimeField(default=timezone.now)
    minutes = models.IntegerField(default=0)

    @property
    def price(self) -> int:
        if self.price_billed:
            return self.price_billed
        if self.price_override:
            return self.price_override

        return self.minutes * self.price_per_minute

    @property
    def price_per_minute(self) -> int:
        return LasercutMinutePrice.objects.get(role=self.order.user.role).price_per_minute

    @property
    def price_per_minute_float(self) -> float:
        return self.price_per_minute / 100.0

    @property
    def price_per_minute_str(self) -> str:
        return f"{self.price_per_minute_float:.2f}".replace(".", ",")

    @property
    def price_per_minute_valuestr(self) -> str:
        return f"{self.price_per_minute_float:.2f}"

    @property
    def filename(self) -> str:
        # type doesn't get inferred correctly for some reason
        file = cast("models.FieldFile", self.file)
        if not file:
            return "[deleted]"
        return file.name.split("/")[-1]

    @property
    def filename_short(self) -> str:
        if len(filename := self.filename) < 20:
            return filename
        return f"{filename[:18]}..."

    @property
    def filename_extended(self) -> str:
        order = self.order
        user = order.user
        if user.matr_nr:
            return f"{order.id}_{user.matr_nr}_{user.last_name}_{self.filename}"
        else:
            return f"{order.id}_{user.last_name}_{self.filename}"

    def __str__(self) -> str:
        return "Laserarbeiten je Minute"


@receiver(models.signals.post_delete, sender=SubOrderLaserCut)
def delete_lasercut_file_on_suborder_delete(
    sender: Type[SubOrderLaserCut], instance: SubOrderLaserCut, **kwargs: Any
) -> None:
    file = cast("models.FieldFile", instance.file)
    if file and os.path.isfile(file.path):
        try:
            os.remove(file.path)
        except Exception as e:
            print(f"delete_lasercut_file_on_suborder_delete: an Exception occured\n{e}")


class SubOrderMaterial(SubOrder):
    material = models.ForeignKey(MaterialVariation, on_delete=models.RESTRICT, related_name="+")
    amount = models.IntegerField()
    associated_lasercut = models.ForeignKey(
        SubOrderLaserCut,
        null=True,
        blank=True,
        default=None,
        on_delete=models.CASCADE,
        related_name="parts",
    )
    size_length = models.IntegerField(null=True, blank=True)
    size_width = models.IntegerField(null=True, blank=True)

    @property
    def price(self) -> int:
        if self.price_billed:
            return self.price_billed
        if self.price_override:
            return self.price_override
        return self.price_per_piece * self.amount

    def __str__(self) -> str:
        return str(self.material)

    @property
    def length(self) -> int:
        value = self.material.length if self.material.is_fixed else self.size_length
        assert value is not None
        return value

    @property
    def width(self) -> int:
        value = self.material.width if self.material.is_fixed else self.size_width
        assert value is not None
        return value

    @property
    def price_per_piece(self) -> int:
        if self.material.is_fixed:
            return self.material.price

        area: int = self.length * self.width
        price: int = self.material.price
        cost: float = float(area * price) / 1e6

        return math.ceil(cost)

    def price_per_piece_float(self) -> float:
        return self.price_per_piece / 100.0

    @property
    def price_per_piece_valuestr(self) -> str:
        return f"{(self.price_per_piece / 100.0):.2f}"


class Billing(CustomBaseModel):
    date_billed = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(ExtendedUser, on_delete=models.RESTRICT)

    @property
    def get_all_billing_orders(self) -> models.QuerySet["BillingOrder"]:
        return BillingOrder.objects.filter(billing=self)


class BillingOrder(CustomBaseModel):
    billing = models.ForeignKey(Billing, on_delete=models.CASCADE)
    order = models.ForeignKey(
        Order, on_delete=models.RESTRICT
    )  # already billed orders can't be deleted


class Message(CustomBaseModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    sender = models.ForeignKey(ExtendedUser, on_delete=models.RESTRICT)
    text = models.TextField()
    date_sent = models.DateTimeField(default=timezone.now)
    new_message = models.BooleanField(default=True)


class WorkshopInformation(CustomBaseModel):
    descriptor = models.CharField(max_length=200)
    value = models.CharField(max_length=200)

    def __str__(self) -> str:
        return f"{self.descriptor}: {self.value}"
