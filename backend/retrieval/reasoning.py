from typing import List, Dict, Any
from datetime import datetime
from backend.utils.llm_client import call_llm
from backend.config import MODEL_MAIN, CONFIDENCE_THRESHOLD
from backend.retrieval.search import search_memory
from backend.verification.validator import Validator

class ReasoningEngine:
    def __init__(self):
        self.validator = Validator()

    def process_query(self, query: str) -> Dict[str, Any]:
        """
        End-to-end query processing: intent, retrieval, synthesis, verification.
        """
        # 1. Intent Detection
        intent = self._detect_intent(query)
        
        # 2. Retrieval
        if intent == "action_list":
             # Need special handler for action items
             pass # For now, treat as general search + summary? Or separate SQL.
        
        context_docs = search_memory(query)
        context_str = self._format_context(context_docs)
        
        if not context_docs:
            return {
                "answer": "I found no relevant information in my memory regarding your query.",
                "confidence": 0,
                "citations": [],
                "intent": intent,
                "uncertainty_flags": ["no_evidence"]
            }

        # 3. Generate Draft Answer
        draft = self._generate_answer(query, context_str)
        
        # 4. Verification Pass
        verification = self.validator.verify(query, draft, context_docs)
        
        final_answer = draft
        if verification["confidence"] < CONFIDENCE_THRESHOLD:
            final_answer += f"\n\n[Warning: Confidence is low ({verification['confidence']}%) due to insufficient evidence or conflicting information.]"
            if "uncertainty_flags" in verification:
                flags = ", ".join(verification["uncertainty_flags"])
                final_answer += f" Reason: {flags}"
        
        return {
            "answer": final_answer,
            "confidence": verification["confidence"],
            "citations": [d["id"] for d in context_docs], # Simply cite context for now, or refine
            "intent": intent,
            "uncertainty_flags": verification.get("uncertainty_flags", [])
        }

    def _detect_intent(self, query: str) -> str:
        prompt = f"""
        Classify the intent of this query into one of: [question, find, summarize, action_list].
        Query: "{query}"
        Return ONLY the label.
        """
        return call_llm(MODEL_MAIN, prompt).strip().lower()

    def _format_context(self, docs: List[Dict[str, Any]]) -> str:
        formatted = ""
        for i, doc in enumerate(docs):
            formatted += f"Source {i+1} (ID: {doc['id']}):\n{doc['text'][:500]}...\n---\n"
        return formatted

    def _generate_answer(self, query: str, context: str) -> str:
        system_prompt = f"""
        You are AI MINDS, an intelligent assistant. Answer the user's question based strictly on the provided context.
        context:
        {context}
        
        If the answer is not in the context, say "I don't know based on the available information."
        Do not hallucinate. Cite sources implicitly by referencing the content.
        Today's date is {datetime.now().strftime('%Y-%m-%d')}.
        """
        
        prompt = f"Question: {query}\nAnswer:"
        return call_llm(MODEL_MAIN, prompt, system=system_prompt)
