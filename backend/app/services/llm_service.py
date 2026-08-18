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
    Supports Google Gemini API SDK & HTTP REST endpoints with fallback.
    """

    @staticmethod
    def _generate_fallback_response(
        context: Dict[str, Any], message: str = "AI analysis is temporarily unavailable. You can still use the map and verified geographic information."
    ) -> Dict[str, Any]:
        """
        Returns structured fallback response when LLM API key is missing or service is offline.
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
        Sends safety context payload to LLM (Google Gemini / OpenAI compatible) and returns verified JSON.
        """
        api_key = settings.GEMINI_API_KEY or settings.LLM_API_KEY
        if not api_key:
            logger.warning("No GEMINI_API_KEY or LLM_API_KEY configured. Returning structured fallback.")
            return LLMService._generate_fallback_response(
                context, message="AI analysis fallback active (Gemini API Key not set). You can still view verified map data."
            )

        prompt_user = f"User Request: {user_query or 'Analyze safety information for this location.'}\n\nSafety Context JSON:\n{json.dumps(context, indent=2)}"

        # 1. Try Google Gemini API (via google-genai SDK or REST API)
        try:
            # Try google-genai SDK
            try:
                from google import genai
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model=settings.LLM_MODEL or "gemini-1.5-flash",
                    contents=SYSTEM_PROMPT + "\n\n" + prompt_user
                )
                if response and response.text:
                    parsed = LLMService._parse_structured_json(response.text)
                    if parsed:
                        return parsed
            except Exception as sdk_err:
                logger.debug(f"google-genai SDK attempt info: {sdk_err}. Falling back to REST API.")

            # Try Gemini REST API directly
            model_name = settings.LLM_MODEL or "gemini-1.5-flash"
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
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
            res = requests.post(url, headers=headers, json=payload, timeout=15)
            if res.status_code == 200:
                res_json = res.json()
                candidates = res_json.get("candidates", [])
                if candidates:
                    text_out = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    parsed = LLMService._parse_structured_json(text_out)
                    if parsed:
                        return parsed

        except Exception as e:
            logger.error(f"Gemini LLM API call failed: {e}")

        return LLMService._generate_fallback_response(context)

    @staticmethod
    def _parse_structured_json(text_out: str) -> Optional[Dict[str, Any]]:
        """
        Parses and validates LLM JSON response matching expected structure.
        """
        try:
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
