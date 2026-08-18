import json
import re
import requests
from typing import Any, Dict, List, Optional
from app.core.config import settings
from app.core.logging import logger

SYSTEM_PROMPT = """You are SafeHer AI Intelligence Assistant for Women's Safety.
Your task is to summarize and explain ONLY the VERIFIED data provided in the Safety Context JSON below.

CRITICAL ANTI-HALLUCINATION RULES:
1. Use ONLY the verified data provided in the Safety Context.
2. NEVER invent or fabricate crime incidents, statistics, police stations, hospitals, phone numbers, or risk scores.
3. If information is missing or empty, explicitly state: "Reliable information is not available for this request."
4. NEVER label an area as "dangerous" or "unsafe" without verified evidence from the supplied context.
5. NEVER generate unsupported numerical risk scores.
6. You MUST output ONLY valid JSON matching this exact structure:
{
  "summary": "Summary based on the available verified data.",
  "key_factors": ["Verified factor 1", "Verified factor 2"],
  "data_limitations": ["Data limitation or empty dataset note"],
  "sources": [{"claim": "Description of claim", "source": "Source database", "period": "Timeframe"}]
}
"""


class LLMService:
    """
    LLM Intelligence Service with Anti-Hallucination Enforcement.
    Communicates with LLM providers (Gemini / OpenAI API compatible) or returns clean fallbacks.
    """

    @staticmethod
    def _generate_fallback_response(
        context: Dict[str, Any], message: str = "AI analysis is temporarily unavailable. You can still use the map and verified geographic information."
    ) -> Dict[str, Any]:
        """
        Returns structured fallback response when LLM service is unavailable or unconfigured.
        Guarantees that the application never crashes and Phases 1-4 continue working 100%.
        """
        incident_count = context.get("nearby_verified_incidents_count", 0)
        police_dist = context.get("nearest_police_station_distance_meters")
        hosp_dist = context.get("nearest_hospital_distance_meters")

        factors = []
        if police_dist is not None:
            factors.append(f"Nearest police station is {police_dist} meters away.")
        if hosp_dist is not None:
            factors.append(f"Nearest hospital is {hosp_dist} meters away.")
        if incident_count > 0:
            factors.append(f"{incident_count} verified crime incidents recorded within search radius.")
        else:
            factors.append("Zero verified crime incidents recorded within search radius.")

        limitations = []
        if incident_count == 0:
            limitations.append("No verified crime incidents recorded in database within search radius.")

        return {
            "summary": message,
            "key_factors": factors if factors else ["Verified PostGIS geographic data active on map."],
            "data_limitations": limitations if limitations else ["LLM service fallback active."],
            "sources": [
                {
                    "claim": f"{incident_count} verified crime incidents recorded within radius.",
                    "source": "Supabase PostgreSQL + PostGIS",
                    "period": "Current database records"
                }
            ]
        }

    @staticmethod
    def analyze_safety_context(
        context: Dict[str, Any], user_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sends safety context payload to LLM and returns verified structured JSON response.
        Enforces strict fallbacks when LLM API keys are missing or timeout occurs.
        """
        api_key = settings.LLM_API_KEY or settings.GEMINI_API_KEY
        if not api_key:
            logger.warning("No LLM_API_KEY or GEMINI_API_KEY set in environment. Returning structured fallback response.")
            return LLMService._generate_fallback_response(
                context, message="AI analysis fallback active (LLM API key not configured). You can still view verified map data."
            )

        prompt_user = f"User Request: {user_query or 'Analyze safety information for this location.'}\n\nSafety Context JSON:\n{json.dumps(context, indent=2)}"

        try:
            # 1. Attempt Gemini API endpoint call
            if settings.GEMINI_API_KEY or "gemini" in settings.LLM_MODEL.lower():
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.LLM_MODEL}:generateContent?key={api_key}"
                headers = {"Content-Type": "application/json"}
                payload = {
                    "contents": [
                        {
                            "parts": [
                                {"text": SYSTEM_PROMPT + "\n\n" + prompt_user}
                            ]
                        }
                    ],
                    "generationConfig": {
                        "temperature": 0.1,
                        "maxOutputTokens": 800,
                        "responseMimeType": "application/json"
                    }
                }
                res = requests.post(url, headers=headers, json=payload, timeout=12)

                if res.status_code == 200:
                    res_json = res.json()
                    candidates = res_json.get("candidates", [])
                    if candidates:
                        text_out = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        parsed = LLMService._parse_structured_json(text_out)
                        if parsed:
                            return parsed

            # 2. Attempt OpenAI-compatible endpoint call
            elif settings.LLM_BASE_URL:
                url = f"{settings.LLM_BASE_URL.rstrip('/')}/chat/completions"
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                }
                payload = {
                    "model": settings.LLM_MODEL,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt_user}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 800
                }
                res = requests.post(url, headers=headers, json=payload, timeout=12)
                if res.status_code == 200:
                    text_out = res.json().get("choices", [{}])[0].get("message", {}).get("content", "")
                    parsed = LLMService._parse_structured_json(text_out)
                    if parsed:
                        return parsed

        except Exception as e:
            logger.error(f"LLM API request error: {e}")

        # Fallback if API request failed or JSON was invalid
        return LLMService._generate_fallback_response(context)

    @staticmethod
    def _parse_structured_json(text_out: str) -> Optional[Dict[str, Any]]:
        """
        Parses and validates LLM JSON response matching expected structure.
        """
        try:
            # Strip markdown code blocks if present
            cleaned = re.sub(r"^```json\s*", "", text_out.strip())
            cleaned = re.sub(r"\s*```$", "", cleaned)
            data = json.loads(cleaned)

            if "summary" in data and "key_factors" in data:
                return {
                    "summary": str(data.get("summary")),
                    "key_factors": list(data.get("key_factors", [])),
                    "data_limitations": list(data.get("data_limitations", [])),
                    "sources": list(data.get("sources", []))
                }
        except Exception as e:
            logger.warning(f"Failed to parse LLM structured JSON output: {e}")

        return None
