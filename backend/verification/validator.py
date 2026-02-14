from typing import Dict, Any, List
from backend.utils.llm_client import call_llm
from backend.config import MODEL_BACKUP

class Validator:
    def verify(self, query: str, answer: str, evidence: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Verify the answer against the provided evidence using a second opinion LLM.
        Returns a dictionary with confidence score (0-100) and flags.
        """
        
        # 1. Structure the check
        evidence_text = "\n".join([f"- {d['text'][:200]}..." for d in evidence])
        
        prompt = f"""
        Review the following AI-generated answer to a user's question, given the provided evidence.
        
        User Question: "{query}"
        AI Answer: "{answer}"
        
        Evidence from Memory:
        {evidence_text}
        
        Task:
        1. Does the evidence support the answer? Yes/No/Partial.
        2. Are there any hallucinations (claims not in evidence)? Yes/No.
        3. Assign a confidence score (0-100) to the answer based on support.
        
        Format your response as valid JSON:
        {{
            "supported": "Yes/No/Partial",
            "hallucination": "Yes/No",
            "confidence_score": <int>,
            "reasoning": "brief explanation"
        }}
        """
        
        # Use Backup model (Phi) for second opinion if available, else Main
        model = MODEL_BACKUP
        response_str = call_llm(model, prompt, json_mode=True)
        
        try:
            import json
            # Simple cleanup if JSON mode fails slightly
            start = response_str.find("{")
            end = response_str.rfind("}")
                flags = []
                if data.get("hallucination", "No").lower() == "yes":
                    flags.append("potential_hallucination")
                if data.get("supported", "Yes").lower() != "yes":
                    flags.append("not_fully_supported")
                    
                return {
                    "confidence": int(data.get("confidence_score", 50)),
                    "supported": data.get("supported", "Unknown"),
                    "hallucination": data.get("hallucination", "Unknown"),
                    "uncertainty_flags": flags,
                    "reasoning": data.get("reasoning", "")
                }
        except Exception:
            pass
            
        # Fallback if verification fails
        return {
            "confidence": 50, 
            "uncertainty_flags": ["verification_failed"],
            "reasoning": "Verification failed to parse."
        }
