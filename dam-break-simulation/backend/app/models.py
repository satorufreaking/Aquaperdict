from pydantic import BaseModel, Field, field_validator
from typing import Literal

class Scenario(BaseModel):
    name: str = Field(default="Demo rapid breach", min_length=2, max_length=80)
    dam_name: str = "Suryanagar Demonstration Dam"
    river_name: str = "Kaveri Tributary (synthetic)"
    dam_height_m: float = Field(default=42, gt=0, le=300)
    reservoir_level_m: float = Field(default=36, gt=0, le=300)
    reservoir_volume_m3: float = Field(default=6_000_000, gt=0)
    breach_width_m: float = Field(default=38, gt=0, le=1000)
    breach_depth_m: float = Field(default=24, gt=0, le=300)
    breach_formation_min: float = Field(default=20, gt=0, le=1440)
    downstream_depth_m: float = Field(default=0.5, ge=0, le=20)
    manning_n: float = Field(default=0.035, gt=0.005, le=0.2)
    duration_min: int = Field(default=180, ge=10, le=720)
    timestep_s: float = Field(default=5, gt=0.5, le=60)

    @field_validator("breach_depth_m")
    @classmethod
    def breach_within_dam(cls, value, info):
        if "dam_height_m" in info.data and value > info.data["dam_height_m"]:
            raise ValueError("Breach depth cannot exceed dam height")
        return value

class CompareRequest(BaseModel):
    scenario_ids: list[str] = Field(min_length=2, max_length=5)

class LayerQuery(BaseModel):
    simulation_id: str
    layer: Literal["depth", "velocity", "arrival", "elevation", "risk"] = "depth"
