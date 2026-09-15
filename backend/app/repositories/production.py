from pydantic import BaseModel


class ProductionState(BaseModel):
    target: float = 1000
    source: str = "demo_in_memory"


class ProductionRepository:
    def get_overview(self) -> ProductionState:
        return ProductionState()
