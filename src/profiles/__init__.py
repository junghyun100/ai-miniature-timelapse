"""
Profile implementations for AI Miniature Timelapse v2.0

Profiles per Section 13:
- architecture.korean (REFERENCE_FRAME_RELAY, 30/60s)
- vehicle.assembly (SINGLE_CLIP_FROM_MASTER, 10s)
- product.assembly (duration-specific single clip or reference-frame relay)
- home_decor.diy (SINGLE_CLIP_FROM_MASTER, 10s, Korean narration)
- cooking.miniature (REFERENCE_FRAME_RELAY, 30s, ASMR only)
"""

from .architecture import architecture_profile
from .home_decor import home_decor_profile
from .cooking import cooking_profile
from .product import product_profile

# Vehicle profile has sub-profiles
from .vehicle import vehicle_profile, VehicleSubtype

__all__ = [
    "architecture_profile",
    "vehicle_profile",
    "VehicleSubtype",
    "product_profile",
    "home_decor_profile",
    "cooking_profile",
]
