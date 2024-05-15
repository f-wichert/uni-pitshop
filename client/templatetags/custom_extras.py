from typing import Any, Dict, List

from django import template
from django.db import models

from model.models import Material

register = template.Library()


@register.inclusion_tag("material_information.html")
def include_material_information() -> Dict[str, Any]:
    materials: models.QuerySet[Material] = Material.objects.filter(is_material_available=True)
    materialArray: List[Dict[str, Any]] = []
    for material in materials:
        variationArray = []
        for variation in material.variations.filter(is_variation_available=True):
            variationArray.append(
                {
                    "variation_id": variation.id,
                    "material_id": variation.base.id,
                    "thickness": variation.thickness,
                    "price": variation.price,
                    "length": variation.length,
                    "width": variation.width,
                    "is_lasercutable": variation.is_lasercutable,
                }
            )
        materialArray.append(
            {
                "material_id": material.id,
                "name": material.name,
                "is_fixed": material.is_fixed_size,
                "needs_comment": material.needs_comment,
                "material_tooltip": material.material_tooltip or "",
                "has_lasercutable_variation": material.has_lasercutable_variation,
                "variationArray": variationArray,
            }
        )

    return {"data": materialArray}
