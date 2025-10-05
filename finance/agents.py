import json
import os
from typing import Any, Dict, List

from openai import OpenAI
from decouple import config as env_config
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpRequest


# Deterministic computation used by the tool call
ASSET_KEY_TO_RETURN = {
    "equity": "equityReturnAnnualPct",
    "bond": "bondReturnAnnualPct",
    "cash": "cashReturnAnnualPct",
    "alt": "altReturnAnnualPct",
}


def _ann_to_monthly(r: float) -> float:
    return (1 + r) ** (1 / 12) - 1


def compute_projection(args: Dict[str, Any]) -> Dict[str, Any]:
    current_age = int(args["currentAge"])
    target_age = int(args["targetRetirementAge"])
    start_year = int(args.get("startCalendarYear", 2025))
    horizon_years = int(args.get("horizonYears", max(0, target_age - current_age)))
    life_expectancy_age = int(args.get("lifeExpectancyAge", current_age + horizon_years))
    include_schedule = bool(args.get("includeSchedule", True))
    granularity = args.get("scheduleGranularity", "monthly")
    stop_when_depleted = bool(args.get("stopWhenDepleted", True))
    monthly_contrib = float(args["monthlyContributions"])
    monthly_expenses = float(args.get("monthlyExpenses", 0.0))

    breakdown = args["portfolioBreakdown"]
    assumptions = args["assumptions"]
    swr = float(assumptions["swrPct"]) / 100.0
    rebalance_every = int(assumptions.get("rebalanceFrequencyMonths", 12))

    asset_mret = {}
    for a in breakdown:
        k = a["assetClass"]
        ann = float(assumptions.get(ASSET_KEY_TO_RETURN[k], 0.0)) / 100.0
        asset_mret[k] = _ann_to_monthly(ann)

    by_asset = {a["assetClass"]: float(a["balance"]) for a in breakdown}
    total_init = sum(by_asset.values()) or 1.0
    target_weights = {k: v / total_init for k, v in by_asset.items()}

    def rebalance():
        total = sum(by_asset.values()) or 0.0
        if total <= 0:
            for k in by_asset:
                by_asset[k] = 0.0
            return
        for k, w in target_weights.items():
            by_asset[k] = total * w

    months_total = min((life_expectancy_age - current_age) * 12, horizon_years * 12)
    retirement_m = max(0, (target_age - current_age) * 12)

    results: List[Dict[str, Any]] = []
    age = current_age
    year = start_year
    sustainable = None
    estimated_exhaustion_age = None

    def total_balance() -> float:
        return sum(by_asset.values())

    for m in range(months_total):
        # contributions vs withdrawals
        if m < retirement_m:
            contrib = monthly_contrib
            withdrawal = 0.0
        else:
            contrib = 0.0
            if sustainable is None:
                sustainable = (total_balance() * swr) / 12.0
            withdrawal = monthly_expenses if monthly_expenses > 0 else sustainable

        total_before = total_balance()
        if total_before > 0:
            for k in list(by_asset.keys()):
                w = by_asset[k] / total_before
                by_asset[k] += contrib * w
                by_asset[k] -= withdrawal * w
                by_asset[k] = max(0.0, by_asset[k])

        for k in list(by_asset.keys()):
            by_asset[k] *= (1 + asset_mret.get(k, 0.0))

        end_bal = total_balance()

        if rebalance_every and (m + 1) % rebalance_every == 0:
            rebalance()

        if end_bal <= 0 and estimated_exhaustion_age is None:
            estimated_exhaustion_age = age
            if stop_when_depleted:
                if include_schedule and granularity == "monthly":
                    ym = (m // 12)
                    results.append(
                        {
                            "yearIndex": ym,
                            "monthIndex": (m % 12) + 1,
                            "calendarYear": year + ym,
                            "calendarMonth": (m % 12) + 1,
                            "age": age,
                            "phase": "retirement" if m >= retirement_m else "accumulation",
                            "contributions": contrib,
                            "withdrawals": withdrawal,
                            "endBalance": end_bal,
                        }
                    )
                break

        if include_schedule:
            if granularity == "monthly":
                ym = m // 12
                results.append(
                    {
                        "yearIndex": ym,
                        "monthIndex": (m % 12) + 1,
                        "calendarYear": year + ym,
                        "calendarMonth": (m % 12) + 1,
                        "age": current_age + ym,
                        "phase": "retirement" if m >= retirement_m else "accumulation",
                        "contributions": contrib,
                        "withdrawals": withdrawal,
                        "endBalance": end_bal,
                    }
                )
            else:
                if (m + 1) % 12 == 0:
                    yi = (m + 1) // 12 - 1
                    results.append(
                        {
                            "yearIndex": yi,
                            "calendarYear": year + yi,
                            "age": current_age + yi,
                            "phase": "retirement" if (m + 1) > retirement_m else "accumulation",
                            "endBalance": end_bal,
                        }
                    )

        if (m + 1) % 12 == 0:
            age += 1

    portfolio_at_retirement = None
    if include_schedule:
        if granularity == "monthly":
            idx = max(0, retirement_m - 1)
            if idx < len(results):
                portfolio_at_retirement = results[idx]["endBalance"]
        else:
            yrs_to_ret = max(0, target_age - current_age) - 1
            if 0 <= yrs_to_ret < len(results):
                portfolio_at_retirement = results[yrs_to_ret]["endBalance"]

    metrics = {
        "portfolioAtRetirement": portfolio_at_retirement,
        "sustainableMonthlySpend": None if sustainable is None else sustainable,
        "estimatedExhaustionAge": estimated_exhaustion_age,
        "successProbabilityPct": None,
    }
    return {"metrics": metrics, "projectionResults": results}


class AgentsService:
    """Wrapper to interact with OpenAI Assistants API using a local tool."""

    def __init__(self, api_key: str | None = None):
        key = api_key or os.environ.get("OPENAI_API_KEY") or env_config("OPENAI_API_KEY", default=None)
        if not key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        self.client = OpenAI(api_key=key)
        # Create or use ephemeral assistant each call; for prod, persist ID
        self.assistant = self.client.beta.assistants.create(
            model="gpt-4o-mini",
            instructions=(
                "Eres un asesor de jubilación. No calcules números; "
                "siempre invoca compute_projection con includeSchedule:true y scheduleGranularity:'monthly'."
            ),
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "compute_projection",
                        "description": "Deterministic projection with schedule",
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "additionalProperties": True,
                        },
                    },
                }
            ],
        )

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        thread = self.client.beta.threads.create()
        self.client.beta.threads.messages.create(
            thread_id=thread.id, role="user", content=json.dumps(payload)
        )
        run = self.client.beta.threads.runs.create(
            thread_id=thread.id, assistant_id=self.assistant.id
        )

        # Poll for tool calls and completion
        while True:
            run = self.client.beta.threads.runs.retrieve(
                thread_id=thread.id, run_id=run.id
            )
            status = run.status
            if status == "requires_action":
                tool_calls = run.required_action.submit_tool_outputs.tool_calls
                outputs = []
                for tc in tool_calls:
                    if tc.type == "function" and tc.function.name == "compute_projection":
                        args = json.loads(tc.function.arguments or "{}")
                        # Merge assistant-provided args over the original payload
                        merged = {**payload, **args}
                        # Ensure schedule defaults
                        merged.setdefault("includeSchedule", True)
                        merged.setdefault("scheduleGranularity", "monthly")
                        result = compute_projection(merged)
                        outputs.append(
                            {"tool_call_id": tc.id, "output": json.dumps(result)}
                        )
                self.client.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread.id, run_id=run.id, tool_outputs=outputs
                )
            elif status in ("completed", "failed", "cancelled", "expired"):
                break

        # Collect assistant message and optionally parse last JSON reflected
        msgs = self.client.beta.threads.messages.list(thread_id=thread.id)
        agent_message = ""
        for m in msgs.data:
            if m.role == "assistant":
                # Concatenate text parts
                parts = []
                for c in m.content:
                    if getattr(c, "type", None) == "text":
                        parts.append(c.text.value)
                if parts:
                    agent_message = "\n".join(parts)
                break

        # Note: the tool result is not auto-reflected; return only message plus no data.
        # In a production setup, instruct the assistant to mirror the JSON or keep the tool_result separately.
        return {"agentMessage": agent_message}


@csrf_exempt
def agents_projection_view(request: HttpRequest):
    """HTTP endpoint that proxies to the AgentsService and returns agentMessage and tool JSON if needed.

    Expected JSON body: matches the compute_projection payload. This endpoint will
    run the assistant, satisfy tool calls locally, and return the assistant message
    along with the raw tool result under `toolResult` for frontend consumption.
    """
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
        service = AgentsService()
        # Run once to get the assistant message; also compute tool locally for the response
        # so the frontend can render charts without relying on the assistant to mirror JSON.
        tool_result = compute_projection({
            **payload,
            "includeSchedule": payload.get("includeSchedule", True),
            "scheduleGranularity": payload.get("scheduleGranularity", "monthly"),
        })
        agent_output = service.run(payload)
        return JsonResponse({**agent_output, "toolResult": tool_result}, status=200)
    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=400)
