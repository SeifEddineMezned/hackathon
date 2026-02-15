from typing import Dict, Any, List
from backend.utils.llm_client import call_llm
from backend.config import MODEL_BACKUP

class Validator:
    def verify(self, query: str, answer: str, evidence: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Verify the answer against the provided evidence using a second opinion LLM to ensure grounding.
        Returns detailed validation result with confidence scoring.
        """
        
        # 1. Structure the evidence
        evidence_content = "\n".join([f"- {d['text'][:300]} (ID: {d['id']})" for d in evidence])
        if not evidence_content:
            return {
                "confidence": 0,
                "supported_claims": [],
                "unsupported_claims": [{"claim": "All", "reason": "No evidence found."}],
                "uncertainty_flags": ["missing_evidence"],
                "reasoning": "No relevant documents found in memory."
            }

        prompt = f"""
        You are a strict fact-checker. 
        Validate the AI Answer against the Evidence provided.
        Identify supported claims and unsupported hallucinations.

        User Question: "{query}"
        AI Answer: "{answer}"
        
        Evidence from Memory:
        {evidence_content}
        
        Return strict JSON analysis:
        {{
            "supported_claims": [
                {{"claim": "exact quote or summary", "evidence_ids": ["ID1", "ID2"]}}
            ],
            "unsupported_claims": [
                {{"claim": "statement not found in evidence", "reason": "why"}} 
            ],
            "contradictions": [
                {{"claim": "statement conflicting with evidence", "conflicting_evidence_ids": ["ID3"]}}
            ],
            "needs_followup_questions": ["question 1"],
            "confidence_score": <int 0-100>,
            "uncertainty_flags": ["missing_evidence"|"conflict"|"low_agreement"|...]
        }}
        """
        
        # Use Backup model (Phi) for validation logic
        model = MODEL_BACKUP
        
        # Retry logic for JSON validation
        for _ in range(2):
            response_str = call_llm(model, prompt, json_mode=True)
            data = self._parse_json(response_str)
            if data and "confidence_score" in data:
                return self._finalize_result(data)
                
        # Final fallback
        return {
            "confidence": 35, 
            "supported_claims": [],
            "unsupported_claims": [{"claim": "Analysis Failed", "reason": "Validator produced invalid JSON."}],
            "uncertainty_flags": ["verification_failed"],
            "reasoning": "Validator produced invalid JSON."
        }

    def _parse_json(self, text: str) -> Dict[str, Any]:
        """Robust JSON extraction."""
        import json
        try:
            # Try finding first { and last }
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                return json.loads(text[start:end+1])
            return json.loads(text)
        except:
            return None

    def _finalize_result(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Consistent scoring policy."""
        score = 85 # Base score
        flags = []
        
        unsupported = data.get("unsupported_claims", [])
        contradictions = data.get("contradictions", [])
        
        # Ensure unsupported_claims is a list of dicts
        safe_unsupported = []
        for x in unsupported:
            if isinstance(x, str):
                safe_unsupported.append({"claim": x, "reason": "Unsupported"})
            else:
                safe_unsupported.append(x)
        
        if safe_unsupported:
            score -= 20
            flags.append("potential_hallucination")
        if contradictions:
            score -= 25
            flags.append("contradiction_detected")
            
        supported = data.get("supported_claims", [])
        if len(supported) < 1 and not safe_unsupported:
            score -= 10
            flags.append("weak_evidence")
            
        # Clamp
        score = max(0, min(100, score))
        
        return {
            "confidence": score,
            "supported_claims": supported,
            "unsupported_claims": safe_unsupported,
            "contradictions": contradictions,
            "uncertainty_flags": flags,
            "needs_followup": data.get("needs_followup_questions", [])
        }
