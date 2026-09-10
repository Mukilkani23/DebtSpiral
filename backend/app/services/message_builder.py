"""
Deterministic, person-specific notification message builder.
PURE: no I/O, no globals, no LLM, no randomness — every number in the
output is read from the structured context passed in.

Kept separate from rules.py by design: rules.py decides the frozen,
API-contract reason_codes (CONTRACTS.md); this module decides ONLY how to
communicate a notification's content. SHAP is never used here — SHAP
explains "why is this user at risk" (model-level), this explains "what
happened with this transaction" (event-level), matching the existing
SHAP/rules separation.

Priority when multiple conditions are true (checked in order): a budget
overage is the most specific, actionable signal, so it wins over a mere
"first time in this category" observation on the same transaction.
"""


def build_message(ctx: dict) -> dict:
    """
    ctx fields (all optional except category/tier/transaction_amount_inr):
      category: str
      tier: int
      transaction_amount_inr: float
      allocated_amount_inr: float
      spent_amount_inr: float          (category total AFTER this transaction)
      remaining_amount_inr: float
      overage_amount_inr: float
      is_new_category: bool
      is_amount_anomaly: bool

    Returns {"event_type": str, "message": str}. event_type "GENERIC" means
    no category-budget-specific situation applied — caller should fall back
    to its existing (non-personalized) nudge behavior.
    """
    category_label = ctx["category"].replace("_", " ").title()
    amount = ctx.get("transaction_amount_inr", 0)

    overage = ctx.get("overage_amount_inr", 0) or 0
    if overage > 0:
        allocated = ctx.get("allocated_amount_inr", 0)
        spent = ctx.get("spent_amount_inr", 0)
        return {
            "event_type": "TIER_BUDGET_EXCEEDED",
            "message": (
                f"\U0001F514 DebtSpiral Alert\n\n"
                f"You've allocated ₹{allocated:,.0f} for {category_label}, "
                f"but you've now spent ₹{spent:,.0f}.\n\n"
                f"That's ₹{overage:,.0f} over your planned limit.\n\n"
                f"Suggestion:\nReduce discretionary spending for the rest of this "
                f"period so your spending stays within your plan."
            ),
        }

    if ctx.get("is_amount_anomaly"):
        return {
            "event_type": "UNPLANNED_EXPENSE",
            "message": (
                f"\U0001F514 Unusual spend detected\n\n"
                f"₹{amount:,.0f} on {category_label} is significantly above "
                f"your usual spending in this category.\n\n"
                f"Suggestion:\nConsider reducing discretionary spending elsewhere."
            ),
        }

    if ctx.get("is_new_category"):
        return {
            "event_type": "UNPLANNED_EXPENSE",
            "message": (
                f"\U0001F514 Unusual spend detected\n\n"
                f"₹{amount:,.0f} on {category_label} is a new spending category "
                f"for you.\n\n"
                f"Suggestion:\nCheck whether this purchase was planned before making "
                f"additional spending in this category."
            ),
        }

    allocated = ctx.get("allocated_amount_inr", 0)
    spent = ctx.get("spent_amount_inr", 0)
    if allocated > 0 and spent > 0.8 * allocated:
        remaining = ctx.get("remaining_amount_inr", max(allocated - spent, 0))
        return {
            "event_type": "TIER_BUDGET_NEAR_LIMIT",
            "message": (
                f"\U0001F4A1 Spending check\n\n"
                f"You've used ₹{spent:,.0f} of your ₹{allocated:,.0f} "
                f"{category_label} allocation.\n\n"
                f"₹{remaining:,.0f} remains.\n\n"
                f"Suggestion:\nKeep the remaining amount for planned spending."
            ),
        }

    if ctx.get("tier") == 3:
        return {
            "event_type": "RESTRICTED_SPEND",
            "message": (
                f"⚠️ Restricted spending\n\n"
                f"₹{amount:,.0f} spent on {category_label}.\n\n"
                f"{category_label} is a Tier 3 restricted category in your current "
                f"plan.\n\n"
                f"Suggestion:\nPause additional restricted spending until your "
                f"essential and discretionary allocations are secure."
            ),
        }

    return {"event_type": "GENERIC", "message": ""}
