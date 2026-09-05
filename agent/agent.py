import json
import os
import uuid
from datetime import datetime

def build_context(state: dict, customers: list) -> dict:
    """
    Assembles a context object from a restaurant_state dict and a list of customer dicts,
    filtering out customers with discount_fatigue_flag=true where at least one
    non-flagged candidate exists.
    """
    non_fatigued = [c for c in customers if not c.get("discount_fatigue_flag", False)]
    
    # If we have at least one non-fatigued customer, use them. Otherwise use all.
    candidates = non_fatigued if non_fatigued else customers
    
    return {
        "restaurant_state": state,
        "candidates": candidates
    }

def fallback_decide(context: dict) -> dict:
    """
    Rule-based fallback for when the API fails.
    """
    state = context.get("restaurant_state", {})
    candidates = context.get("candidates", [])
    
    occupancy_pct = state.get("occupancy_pct", 100)
    cancellations_last_30min = state.get("cancellations_last_30min", 0)
    is_peak_hour = state.get("is_peak_hour", True)
    
    score = (100 - occupancy_pct) * 0.5 + cancellations_last_30min * 15 + (0 if is_peak_hour else 20)
    
    if score < 30:
        decision_type = "no_action"
    elif score <= 55:
        decision_type = "notify_only"
    elif score <= 75:
        decision_type = "low_incentive"
    else:
        decision_type = "high_incentive"
        
    # Pick the first candidate as target (our context builder already prioritizes non-fatigued)
    target_customer_id = candidates[0].get("customer_id") if candidates else None
    
    return {
        "decision": decision_type,
        "target_customer_id": target_customer_id,
        "offer": f"Fallback generated offer for {decision_type}",
        "reasoning": f"Generated via fallback rule engine. Score was {score}."
    }

def _call_llm(prompt: str) -> str:
    """Helper to call LLM, easy to swap providers based on environment variables."""
    if "GEMINI_API_KEY" in os.environ:
        try:
            import google.generativeai as genai
            genai.configure(api_key=os.environ["GEMINI_API_KEY"])
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            return response.text
        except ImportError:
            raise ImportError("google-generativeai package is required. Install it using 'pip install google-generativeai'")
    elif "OPENAI_API_KEY" in os.environ:
        try:
            import openai
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except ImportError:
            raise ImportError("openai package is required. Install it using 'pip install openai'")
    elif "ANTHROPIC_API_KEY" in os.environ:
        try:
            import anthropic
            client = anthropic.Anthropic()
            message = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text
        except ImportError:
            raise ImportError("anthropic package is required. Install it using 'pip install anthropic'")
    else:
        raise ValueError("No API key found for Gemini, OpenAI, or Anthropic.")

def decide(context: dict) -> dict:
    """
    Sends context to an LLM to make a decision. Falls back to a rule-based
    engine if the API call fails or returns malformed JSON.
    """
    system_prompt = (
        "You are a restaurant revenue-management agent. Given the context, decide ONE of: "
        "notify_only, low_incentive, high_incentive, no_action. Guidelines: peak hours rarely "
        "need incentives since tables fill naturally; off-peak + low occupancy + rising "
        "cancellations justifies a stronger incentive; never offer a discount to a customer "
        "flagged discount_fatigue_flag=true, use notify_only or a non-discount nudge instead; "
        "prefer the cheapest lever that plausibly fills the gap (soft nudge < complimentary "
        "item < discount); don't discount when occupancy is merely normal, not empty. Pick "
        "ONE target customer from the candidates. Return ONLY strict JSON, no prose: "
        '{"decision": "...", "target_customer_id": "...", "offer": "...", "reasoning": "2-3 sentences"}'
    )
    
    prompt = f"{system_prompt}\n\nContext:\n{json.dumps(context, default=str)}"
    
    try:
        response_text = _call_llm(prompt)
        
        # Clean up the response if it has markdown code blocks
        clean_text = response_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
            
        decision = json.loads(clean_text.strip())
        
        # Validate expected keys
        expected_keys = {"decision", "target_customer_id", "offer", "reasoning"}
        if not expected_keys.issubset(decision.keys()):
            raise ValueError(f"Missing keys in LLM response. Expected {expected_keys}")
            
        return decision
        
    except Exception as e:
        print(f"LLM decision failed: {e}. Using fallback.")
        return fallback_decide(context)

def log_decision(decision: dict, context: dict) -> None:
    """
    Appends the decision plus a timestamp and the occupancy snapshot to decisions_log.json.
    """
    # Use absolute path resolving relative to this file to find data/decisions_log.json
    log_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'decisions_log.json')
    
    state = context.get("restaurant_state", {})
    occupancy_pct = state.get("occupancy_pct", 0)
    
    entry = {
        "decision_id": f"D{uuid.uuid4().hex[:4].upper()}",
        "timestamp": datetime.now().isoformat(),
        "occupancy_snapshot": occupancy_pct,
        "decision_type": decision.get("decision"),
        "target_customer_id": decision.get("target_customer_id"),
        "offer": decision.get("offer"),
        "reasoning": decision.get("reasoning"),
        "rendered_payload": "..."
    }
    
    logs = []
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r') as f:
                content = f.read().strip()
                if content:
                    logs = json.loads(content)
        except json.JSONDecodeError:
            pass
            
    logs.append(entry)
    
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    with open(log_file, 'w') as f:
        json.dump(logs, f, indent=2)

if __name__ == "__main__":
    # Test execution
    test_context = {
        "restaurant_state": {
            "occupancy_pct": 25,
            "is_peak_hour": False,
            "cancellations_last_30min": 2,
            "cancellations_today": 4
        },
        "candidates": [
            {"customer_id": "C001", "discount_fatigue_flag": True},
            {"customer_id": "C002", "discount_fatigue_flag": False},
            {"customer_id": "C003", "discount_fatigue_flag": False}
        ]
    }
    
    # Example test
    print("Testing Context Builder:")
    ctx = build_context(test_context["restaurant_state"], test_context["candidates"])
    print(json.dumps(ctx, indent=2))
    
    print("\nTesting Fallback Decide:")
    print(json.dumps(fallback_decide(ctx), indent=2))
    
    print("\nTesting Decide (this will use the LLM if API key is in environment, else fallback):")
    decision = decide(ctx)
    print(json.dumps(decision, indent=2))
    
    # Optionally test logging if desired, but we won't execute it to avoid polluting data directory
    # log_decision(decision, ctx)
