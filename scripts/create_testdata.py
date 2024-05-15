import os
import random
import sys
from pathlib import Path

import django
from django.core.files.base import ContentFile


def init_django() -> None:

    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, root_dir)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pitshop.settings")
    django.setup()


def init_db() -> None:
    from django.core import management
    from django.db import connection

    # check uninitialized
    table_names = connection.introspection.table_names()
    assert len(table_names) == 0, "expected uninitialized database"

    # run migrations
    management.call_command("migrate")


init_django()
init_db()

from django.contrib.auth import get_user_model
from django.contrib.auth.models import UserManager

from model.models import (
    ExtendedUser,
    ExtendedUserRole,
    LasercutMinutePrice,
    Material,
    MaterialVariation,
    Order,
    OrderState,
    WorkshopInformation,
)


def create_variable_material(
    name: str, max_length: int, max_width: int, variations: list[tuple[float, int, bool]]
) -> Material:
    mat = Material.objects.create(
        name=name,
        default_length=max_length,
        default_width=max_width,
        is_fixed_size=False,
    )
    MaterialVariation.objects.bulk_create(
        [
            MaterialVariation(base=mat, thickness=t, price=p, is_lasercutable=c)
            for t, p, c in variations
        ]
    )
    return mat


def create_fixed_material(
    name: str,
    default_length: int,
    default_width: int,
    variations: list[tuple[int, int, float, int, bool]],
) -> Material:
    mat = Material.objects.create(
        name=name,
        default_length=default_length,
        default_width=default_width,
        is_fixed_size=True,
    )
    MaterialVariation.objects.bulk_create(
        [
            MaterialVariation(
                base=mat,
                non_default_length=None if x == default_length else x,
                non_default_width=None if w == default_width else w,
                thickness=t,
                price=p,
                is_lasercutable=c,
            )
            for x, w, t, p, c in variations
        ]
    )
    return mat


def generate_mdf_braun_calibrations(
    variations: list[tuple[float, int, bool]]
) -> list[tuple[float, int, bool]]:
    calibrations = []
    markup = 400
    i = len(variations) - 1
    t = 11.5

    while t > 0.5:
        if variations[i - 1][0] == t:
            i -= 1
            t -= 0.5
            markup = 400
            continue

        calibrations.append((t, variations[i][1] + markup, t <= 8.0))
        markup += 200
        t -= 0.5

    return calibrations[::-1]


# create lasercut prices
LasercutMinutePrice.objects.create(role=ExtendedUserRole.INTERNAL_STUDENT, price_per_minute=40)
LasercutMinutePrice.objects.create(role=ExtendedUserRole.EXTERNAL_STUDENT, price_per_minute=60)
LasercutMinutePrice.objects.create(role=ExtendedUserRole.EXTERNAL_CUSTOMER, price_per_minute=100)

# create users
user_manager: UserManager[ExtendedUser] = get_user_model().objects
admin = user_manager.create_superuser(
    username="admin",
    password="eb1fade880aa58e24a09d779601874c7",
    email="admin@localhost",
    first_name="admin",
    last_name="admin",
)

user1 = user_manager.create_user(
    username="user1",
    password="aaccb6e4d53e6bc0ac98f23a5f5376d5",
    email="user1@localhost",
    first_name="Petra",
    last_name="Kortig",
)
user2 = user_manager.create_user(
    username="user2",
    password="0951cb97c517aceeef973b1a44d2c54d",
    email="user2@localhost",
    first_name="Dirk",
    last_name="Förster",
)

# User accounts

jonas_moeler = user_manager.create_user(
    username="jonas-moeler",
    password="jonas-moeler-rocks",
    email="jonasmoeler@gmx.de",
    first_name="Jonas",
    last_name="Moeler",
)

dschinkels = user_manager.create_user(
    username="dschinkels",
    password="dschinkels-rocks",
    email="dschinkels@gmail.com",
    first_name="Daniel",
    last_name="Schinkels",
)

jafre = user_manager.create_user(
    username="jafre",
    password="jafre-rocks",
    email="jafre02@gmx.de",
    first_name="jafre",
    last_name="-",
)

pafre = user_manager.create_user(
    username="pafre",
    password="pafre-rocks",
    email="pafre94@gmx.de",
    first_name="pafre",
    last_name="-",
)


# Admin accounts

tim_wagner = user_manager.create_superuser(
    username="tim-wagner",
    password="tim-wagner-rocks",
    email="Tim.wagner3@stud.tu-darmstadt.de",
    first_name="Tim",
    last_name="Wagner",
)

andreas_noback = user_manager.create_superuser(
    username="andreas-noback",
    password="andreas-noback123",
    email="andreas.noback@architektur.tu-darmstadt.de",
    first_name="Andreas",
    last_name="Noback",
)

peter_maier = user_manager.create_superuser(
    username="peter-maier",
    password="peter-maier123",
    email="pit@architektur.tu-darmstadt.de",
    first_name="Peter",
    last_name="Maier",
)

andreas_benz = user_manager.create_superuser(
    username="andreas-benz",
    password="andreas-benz123",
    email="benz@architektur.tu-darmstadt.de",
    first_name="Andreas",
    last_name="Benz",
)

steffen_heger = user_manager.create_superuser(
    username="steffen-heger",
    password="steffen-heger123",
    email="steffen.heger@gmail.com",
    first_name="Steffen",
    last_name="Heger",
)

nico_weber = user_manager.create_superuser(
    username="nico-weber",
    password="nico-weber123",
    email="nico.weber@outlook.com",
    first_name="Nico",
    last_name="Weber",
)


# TODO: deal with Linde properly
create_variable_material("Linde", 75, 120, [(1000.0, 10, True)])

mdf_braun_variations = [
    (3.0, 1300, True),
    (4.0, 1400, True),
    (5.0, 1500, True),
    (6.0, 1600, True),
    (8.0, 1700, True),
    (10.0, 1800, False),
    (12.0, 2000, False),
]
mdf_braun_calibrations = generate_mdf_braun_calibrations(mdf_braun_variations)
mat_mdf_brown = create_variable_material("MDF braun", 2700, 2050, mdf_braun_variations)
mat_mdf_brown_cal = create_variable_material(
    "MDF braun kalibriert", 2700, 1300, mdf_braun_calibrations
)

mat_mdf_black = create_variable_material("MDF schwarz", 2700, 2050, [(10.0, 2000, False)])

mat_pappel = create_variable_material(
    "Pappelsperrholz",
    2700,
    1700,
    [
        (3.0, 1300, True),
        (4.0, 1400, True),
        (5.0, 1500, True),
        (6.0, 1600, True),
        (8.0, 1700, True),
        (10.0, 1800, True),
        (12.0, 2000, False),
    ],
)

mat_flug = create_variable_material(
    "Flugzeugsperrholz",
    1500,
    1500,
    [
        (1.0, 1000, True),
        (2.0, 1200, True),
    ],
)

mat_grau_pappe = create_fixed_material(
    "Graupappe",
    1050,
    750,
    [
        (1050, 750, 0.5, 1000, True),
        (1050, 750, 1.0, 1100, True),
        (1050, 750, 1.5, 1200, True),
        (1050, 750, 2.0, 1300, True),
        (1050, 750, 2.5, 1400, True),
        (1000, 700, 3.0, 1500, True),
    ],
)

mat_finn_pappe = create_fixed_material(
    "Finnpappe",
    1000,
    700,
    [
        (1000, 700, 1.0, 1000, True),
        (1000, 700, 1.5, 1100, True),
        (1000, 700, 2.0, 1200, True),
        (1000, 700, 2.5, 1300, True),
        (1000, 700, 3.0, 1400, True),
    ],
)

mat_sieb_pappe = create_fixed_material(
    "Siebdruckpappe",
    1000,
    700,
    [
        (1100, 640, 0.5, 1000, True),
        (1000, 700, 1.0, 1000, True),
        (1000, 700, 1.5, 1100, True),
        (1000, 700, 2.0, 1200, True),
        (1000, 700, 2.5, 1300, True),
        (1000, 700, 3.0, 1400, True),
    ],
)

mat_press_pappe = create_fixed_material(
    "Presspappe",
    1000,
    700,
    [
        (1000, 700, 0.5, 1000, True),
        (1000, 700, 1.0, 1200, True),
    ],
)


# create orders
order1 = Order.objects.create(
    user=user1, state=OrderState.IN_PROGRESS, staff_comment="Wartet auf Materiallieferung"
)
order2 = Order.objects.create(
    user=user2,
    state=OrderState.SUBMITTED,
    staff_comment="Diese Bestellung muss langsam geschnitten werden",
)


curr_dir = Path(__file__).parent

# create suborders
suborder_lc1 = order1.suborderlasercut_set.create(
    file=ContentFile((curr_dir / "colors.dxf").read_bytes(), name="lasercut42.dxf"),
    customer_comment=(
        "Diese Datei ist hoffenlich nicht zu groß,\n"
        "ansonsten senden Sie mir gerne eine Nachricht."
    ),
)
suborder_lc1.parts.create(
    order=suborder_lc1.order,
    material=random.choice(list(mat_grau_pappe.variations.all())),
    amount=3,
)
suborder_lc1.parts.create(
    order=suborder_lc1.order,
    material=random.choice(list(mat_flug.variations.all())),
    amount=1,
    size_length=1250,
    size_width=600,
)
suborder_mat1 = order1.subordermaterial_set.create(
    material=random.choice(list(mat_pappel.variations.all())),
    amount=1,
    size_length=2700,
    size_width=1300,
    customer_comment="Am besten nochmal in der Mitte halbiert",
)


suborder_lc2 = order2.suborderlasercut_set.create(
    file=ContentFile((curr_dir / "sketch2d.3dm").read_bytes(), name="sketch2d.3dm"),
)
suborder_lc2.parts.create(
    order=suborder_lc2.order,
    material=random.choice(list(mat_flug.variations.all())),
    amount=3,
    size_length=900,
    size_width=700,
)
suborder_mat2 = order2.subordermaterial_set.create(
    material=random.choice(list(mat_press_pappe.variations.all())),
    amount=3,
)
suborder_mat3 = order2.subordermaterial_set.create(
    material=random.choice(list(mat_mdf_black.variations.all())),
    amount=1,
    size_length=2000,
    size_width=1337,
)
suborder_mat4 = order2.subordermaterial_set.create(
    material=random.choice(list(mat_mdf_brown_cal.variations.all())),
    amount=10,
    size_length=2700,
    size_width=1300,
)


# Insert Workshop Information
WorkshopInformation(descriptor="Straße", value="El-Lissitzky-Str. 1").save()
WorkshopInformation(descriptor="Ort", value="64287 Darmstadt").save()
WorkshopInformation(descriptor="Telefon", value="+49 6151 16-23480").save()
WorkshopInformation(descriptor="Fax", value="+49 6151 16-23480").save()
WorkshopInformation(descriptor="Kontakt", value="pit@architektur.tu-darmstadt.de").save()
WorkshopInformation(descriptor="MwSt", value="19").save()
WorkshopInformation(descriptor="IBAN", value="DE 36508501500000704300").save()
WorkshopInformation(descriptor="Kostenstelle", value="150099").save()
WorkshopInformation(descriptor="Projektnummer", value="90100048").save()
WorkshopInformation(descriptor="KontoNummer", value="704 300").save()
WorkshopInformation(descriptor="BLZ", value="508 501 50").save()
WorkshopInformation(descriptor="Bank", value="Sparkasse Darmstadt").save()
WorkshopInformation(descriptor="ZahlungszielTage", value="14").save()
WorkshopInformation(descriptor="Verantwortlicher", value="Peter Maier").save()
WorkshopInformation(descriptor="UStID", value="DE 111 608 628").save()
WorkshopInformation(descriptor="Steuernummer", value="007 226 001 39").save()
WorkshopInformation(descriptor="Fachbereich", value="Architektur").save()
WorkshopInformation(descriptor="WerkstattName", value="Modellbauwerkstatt").save()
WorkshopInformation(descriptor="Laserschnitt_Aktiv", value="Ja").save()
WorkshopInformation(descriptor="Materialkauf_Aktiv", value="Ja").save()
WorkshopInformation(descriptor="3D_Print_Aktiv", value="Ja").save()
