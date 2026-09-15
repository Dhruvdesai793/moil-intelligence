from app.schemas.decision import Priority, Recommendation, Recommendations
from app.schemas.production import Risk
from app.services.exploration_service import ExplorationService
from app.services.production_service import ProductionService


class DecisionService:
    def __init__(self, production: ProductionService, exploration: ExplorationService):
        self.production = production
        self.exploration = exploration

    def recommendations(self) -> Recommendations:
        overview = self.production.overview()
        sites = self.exploration.get_sites()
        return Recommendations(
            recommendations=[
                Recommendation(
                    priority=Priority.HIGH
                    if overview.risk == Risk.HIGH
                    else Priority.NORMAL,
                    actions=[
                        "Review the demo production schedule with a human planner.",
                        "Obtain validated operational history before making mine decisions.",
                    ],
                    drivers=[
                        f"Demo production risk: {overview.risk.value}",
                        f"Demo active exploration sites: {len(sites)}",
                    ],
                ),
                Recommendation(
                    priority=Priority.NORMAL,
                    actions=[
                        "Validate exploration inputs and baseline before field action."
                    ],
                    drivers=[
                        "Validated geology, drilling assays and trained models unavailable"
                    ],
                ),
            ],
            warning="Demonstration rules only; no causal improvement or mining safety claim. "
            "Human approval required.",
        )
