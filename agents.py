import os
import json
import time
import google.generativeai as genai

class AbstractAnalysisAgents:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)

    def _get_valid_model(self):
        try:
            valid_models = [m.name for m in genai.list_models() if "generateContent" in m.supported_generation_methods]
            if "models/gemini-1.5-pro" in valid_models:
                return "models/gemini-1.5-pro"
            elif valid_models:
                return valid_models[0]
        except Exception as e:
            print(f"Error checking valid models: {e}")
        return "models/gemini-1.5-pro"

    def analyze_abstract_unified(self, abstract_text: str) -> dict:
        if not self.api_key:
            return {"Error": "API Key not set. Please enter a valid Gemini API Key in the settings."}
            
        system_prompt = (
            "You are an expert corpus linguist analyzing an academic abstract using John Swales' CARS (Create A Research Space) model. "
            "Return a strictly valid JSON object adhering to the following rules:\n\n"
            "1. Swales CARS Moves Analysis (HARD SENTENCE-LEVEL RULE & COMPLETE COVERAGE):\n"
            "   - EACH sentence MUST be treated independently and placed in its own JSON object in the moves array.\n"
            "   - ANTI-GROUPING RULE: NEVER combine multiple sentences into one move entry. NEVER summarize multiple sentences.\n"
            "   - ALL sentences must be classified. NO sentence can be skipped. If uncertain, assign the most likely move with LOW confidence (0.3-0.6).\n"
            "   - Move 1 (Background): Assign to general research territory or context.\n"
            "   - Move 2 (Gap/Niche): Mark 'explicit gap' if trigger words are present ('however', 'lack', 'limited'). Otherwise, mark 'implicit niche (low confidence)'.\n"
            "   - Move 3 (Method): Assign to methodology, study design, or data collection.\n"
            "   - Move 4 (Results): MUST be assigned if the sentence contains 'results', 'accuracy', 'performance', or 'evaluation'.\n"
            "   - Move 5 (Conclusion): MUST be assigned if the sentence contains 'future work', 'limitations', 'suggests', 'recommend', or 'may'.\n"
            "   - Assign a strict confidence score (0.0 to 1.0) for every sentence's move.\n\n"
            "2. Hedging Analysis:\n"
            "   - Only count actual modal verbs or hedging expressions (e.g., 'may', 'might', 'could', 'potentially', 'suggests').\n"
            "   - Do NOT overcount or use paraphrased interpretations.\n"
            "   - Provide an overall confidence score for hedging detection.\n\n"
            "3. Academic Tone Constraints:\n"
            "   - Avoid overconfident AI language or hallucinations. DO NOT use phrases like 'clearly demonstrates' or 'proves'.\n"
            "   - Use conservative, evidence-based language: 'suggests', 'indicates', 'based on textual evidence'.\n\n"
            "OUTPUT JSON SCHEMA:\n"
            "{\n"
            "  \"moves\": [{ \"sentence\": \"Single sentence text...\", \"move\": \"Move 1\", \"confidence\": 0.85 }],\n"
            "  \"hedging\": { \"count\": 2, \"words\": [\"may\", \"suggests\"], \"confidence\": 0.90 },\n"
            "  \"summary\": \"Strict, conservative academic summary based on evidence...\",\n"
            "  \"overall_confidence\": 0.88\n"
            "}\n"
            "Format the output strictly as JSON without markdown blocks."
        )
        
        try:
            # Safe initialization check
            model_name = self._get_valid_model()
            
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json"
                )
            )
            
            # Simple throttle to prevent 429 quota exhaustion on free tier
            time.sleep(5)
            
            response = model.generate_content(f"Abstract text:\n\n{abstract_text}")
            
            try:
                # Robust JSON extraction
                text = response.text.strip()
                # If wrapped in markdown code blocks, extract it
                import re
                match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
                if match:
                    text = match.group(1).strip()
                    
                # Parse JSON string into dict
                result = json.loads(text)
                return result
            except json.JSONDecodeError:
                return {"Error": "Failed to parse API response as JSON.", "Raw": response.text}
                
        except Exception as e:
            return {"Error": f"Gemini API Error: {str(e)}"}
