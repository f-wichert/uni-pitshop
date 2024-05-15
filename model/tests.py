import pytest
from django.db import models

from .models import ExtendedUser, Material, MaterialVariation, Order

# user tests


def test_extended_user(django_user_model: models.Model) -> None:
    user = django_user_model.objects.create(tu_id="ab12wxyz", matr_nr=4242424)

    assert isinstance(user, ExtendedUser)
    assert user.tu_id == "ab12wxyz"
    assert user.matr_nr == 4242424


# order tests


@pytest.fixture
def order(admin_user: ExtendedUser) -> Order:
    return Order.objects.create(user=admin_user)


@pytest.fixture
def material() -> Material:
    return Material.objects.create(name="stuff", price=69, max_width=12, max_height=34)


@pytest.fixture
def materialvar(material: Material) -> MaterialVariation:
    return material.variations.create(thickness=3.5)


@pytest.mark.django_db
def test_order(order: Order) -> None:
    assert order.date_ordered  # make sure default value gets set


@pytest.mark.django_db
def test_suborders(order: Order) -> None:
    suborder_lc = order.suborderlasercut_set.create(
        cost=42,
    )

    assert suborder_lc.order == order
    assert order.suborderlasercut_set.count() == 1
    assert order.subordermaterial_set.count() == 0


@pytest.mark.django_db
def test_lasercut_parts(order: Order, materialvar: MaterialVariation) -> None:
    suborder_lc = order.suborderlasercut_set.create(
        cost=42,
    )

    part1 = suborder_lc.parts.create(material=materialvar, amount=4, file_index=2)
    assert part1.suborder == suborder_lc

    suborder_lc.parts.create(material=materialvar, amount=9, file_index=1)

    assert suborder_lc.parts.count() == 2
