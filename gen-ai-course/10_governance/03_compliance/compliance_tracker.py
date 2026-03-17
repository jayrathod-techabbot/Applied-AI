"""
Compliance Tracker Demo

This script demonstrates tracking AI system compliance.
"""

from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional


class RiskLevel(Enum):
    UNACCEPTABLE = "Unacceptable"
    HIGH = "High"
    LIMITED = "Limited"
    MINIMAL = "Minimal"


class ComplianceStatus(Enum):
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    COMPLIANT = "Compliant"
    NON_COMPLIANT = "Non-Compliant"


class AISystem:
    """Represents an AI system for compliance tracking."""

    def __init__(self, name: str, use_case: str, risk_level: RiskLevel):
        self.name = name
        self.use_case = use_case
        self.risk_level = risk_level
        self.status = ComplianceStatus.PENDING
        self.requirements: List[str] = []
        self.completed_requirements: List[str] = []
        self.created_at = datetime.now()
        self.last_review: Optional[datetime] = None

    def add_requirement(self, requirement: str):
        """Add a compliance requirement."""
        self.requirements.append(requirement)

    def complete_requirement(self, requirement: str):
        """Mark a requirement as completed."""
        if requirement in self.requirements:
            self.completed_requirements.append(requirement)

    def get_compliance_percentage(self) -> float:
        """Calculate compliance percentage."""
        if not self.requirements:
            return 0.0
        return len(self.completed_requirements) / len(self.requirements) * 100

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "use_case": self.use_case,
            "risk_level": self.risk_level.value,
            "status": self.status.value,
            "compliance_pct": self.get_compliance_percentage(),
            "requirements_met": f"{len(self.completed_requirements)}/{len(self.requirements)}",
            "created": self.created_at.isoformat(),
            "last_review": (
                self.last_review.isoformat() if self.last_review is not None else None
            ),
        }


class ComplianceTracker:
    """Manages AI compliance across an organization."""

    def __init__(self):
        self.systems: List[AISystem] = []

    def register_system(
        self, name: str, use_case: str, risk_level: RiskLevel
    ) -> AISystem:
        """Register a new AI system."""
        system = AISystem(name, use_case, risk_level)

        # Add default requirements based on risk level
        if risk_level == RiskLevel.HIGH:
            system.add_requirement("Risk assessment completed")
            system.add_requirement("Data governance documented")
            system.add_requirement("Technical specifications")
            system.add_requirement("Human oversight implemented")
            system.add_requirement("Accuracy testing")
            system.add_requirement("Incident response plan")
        elif risk_level == RiskLevel.LIMITED:
            system.add_requirement("Transparency disclosure")
            system.add_requirement("Age verification")
        else:
            system.add_requirement("Basic documentation")

        self.systems.append(system)
        return system

    def get_high_risk_systems(self) -> List[AISystem]:
        """Get all high-risk systems."""
        return [s for s in self.systems if s.risk_level == RiskLevel.HIGH]

    def get_non_compliant_systems(self) -> List[AISystem]:
        """Get systems that are non-compliant."""
        return [s for s in self.systems if s.status == ComplianceStatus.NON_COMPLIANT]

    def generate_report(self) -> str:
        """Generate compliance report."""
        lines = [
            "=" * 60,
            "AI Compliance Report",
            "=" * 60,
            f"Total Systems: {len(self.systems)}",
            f"High Risk: {len(self.get_high_risk_systems())}",
            f"Non-Compliant: {len(self.get_non_compliant_systems())}",
            "",
        ]

        for system in self.systems:
            lines.append(f"\n{system.name}")
            lines.append(f"  Risk Level: {system.risk_level.value}")
            lines.append(f"  Status: {system.status.value}")
            lines.append(f"  Compliance: {system.get_compliance_percentage():.1f}%")

        return "\n".join(lines)

    def export_json(self) -> str:
        """Export all systems as JSON."""
        import json

        return json.dumps([s.to_dict() for s in self.systems], indent=2)


# Demo
if __name__ == "__main__":
    print("=" * 60)
    print("Compliance Tracker Demo")
    print("=" * 60)

    tracker = ComplianceTracker()

    # Register systems
    hiring = tracker.register_system(
        "AI Hiring Assistant", "Employment screening", RiskLevel.HIGH
    )

    chatbot = tracker.register_system(
        "Customer Support Bot", "Customer service", RiskLevel.LIMITED
    )

    recommender = tracker.register_system(
        "Product Recommender", "Product recommendations", RiskLevel.MINIMAL
    )

    # Mark requirements as completed
    hiring.complete_requirement("Risk assessment completed")
    hiring.complete_requirement("Data governance documented")
    hiring.complete_requirement("Technical specifications")

    chatbot.complete_requirement("Transparency disclosure")

    # Print report
    print(tracker.generate_report())

    # Export JSON
    print("\n" + "=" * 60)
    print("JSON Export:")
    print("=" * 60)
    print(tracker.export_json())
