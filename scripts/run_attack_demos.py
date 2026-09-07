"""Run and verify all deterministic AgentShield release attack scenarios."""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.red_team.service import SCENARIOS, run_scenario


async def main() -> None:
    results = []
    for scenario in SCENARIOS:
        execution = await run_scenario(scenario, f"release-{scenario.id}")
        decision = execution.decision
        if decision.outcome != "block" or not decision.reason_codes:
            raise RuntimeError(f"release scenario did not block safely: {scenario.id}")
        results.append(
            {
                "scenario": scenario.id,
                "decision": decision.outcome.upper(),
                "risk_score": decision.risk_score,
                "risk_level": decision.risk_level,
                "reason_codes": list(decision.reason_codes),
            }
        )
    print(json.dumps(results, indent=2))
    print(f"Verified {len(results)} of {len(SCENARIOS)} attack scenarios: all BLOCKED")


if __name__ == "__main__":
    asyncio.run(main())
