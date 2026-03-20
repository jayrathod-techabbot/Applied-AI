"""LLM response quality evaluation using Azure AI Evaluation patterns."""
import logging
import random
from app.config import get_settings
from app.models import EvaluationScore

logger = logging.getLogger(__name__)
settings = get_settings()


class LLMEvaluator:
    """
    Evaluates LLM responses for quality metrics.

    In production, wire this to Azure AI Evaluation SDK or PromptFlow evaluation.
    The heuristic fallbacks here demonstrate the evaluation pipeline structure.
    """

    def should_evaluate(self) -> bool:
        """Sample a fraction of requests for evaluation to control cost."""
        return random.random() < settings.eval_sample_rate

    def evaluate(
        self,
        request_id: str,
        user_query: str,
        assistant_response: str,
        context: str = "",
    ) -> EvaluationScore:
        """
        Run evaluation metrics on a query-response pair.

        Production options:
          - azure.ai.evaluation SDK (coherence, relevance, fluency, groundedness)
          - PromptFlow evaluation runs
          - Custom LLM-as-judge prompts
        """
        coherence = self._eval_coherence(assistant_response)
        relevance = self._eval_relevance(user_query, assistant_response)
        fluency = self._eval_fluency(assistant_response)
        groundedness = self._eval_groundedness(assistant_response, context) if context else None

        scores = [coherence, relevance, fluency]
        if groundedness is not None:
            scores.append(groundedness)
        overall = round(sum(scores) / len(scores), 3)

        score = EvaluationScore(
            request_id=request_id,
            coherence=coherence,
            relevance=relevance,
            fluency=fluency,
            groundedness=groundedness,
            overall=overall,
        )

        logger.info(
            "Evaluation completed",
            extra={
                "request_id": request_id,
                "coherence": coherence,
                "relevance": relevance,
                "fluency": fluency,
                "groundedness": groundedness,
                "overall": overall,
            },
        )
        return score

    # ── Heuristic evaluators (replace with LLM-as-judge in production) ─────

    def _eval_coherence(self, response: str) -> float:
        """Score coherence based on sentence structure heuristics."""
        if not response or len(response) < 10:
            return 0.1
        sentences = [s.strip() for s in response.split(".") if s.strip()]
        if len(sentences) < 1:
            return 0.3
        avg_len = sum(len(s) for s in sentences) / len(sentences)
        # Penalize very short or very long sentences
        score = 1.0 - abs(avg_len - 80) / 200
        return max(0.0, min(1.0, round(score, 3)))

    def _eval_relevance(self, query: str, response: str) -> float:
        """Score relevance by keyword overlap between query and response."""
        query_words = set(query.lower().split())
        response_words = set(response.lower().split())
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "i", "you", "it"}
        query_keywords = query_words - stop_words
        if not query_keywords:
            return 0.5
        overlap = len(query_keywords & response_words) / len(query_keywords)
        return round(min(1.0, overlap * 1.5), 3)  # Scale up slightly

    def _eval_fluency(self, response: str) -> float:
        """Score fluency based on response length and structure."""
        if not response:
            return 0.0
        words = response.split()
        if len(words) < 5:
            return 0.3
        if len(words) > 500:
            return 0.8  # Long but structured
        return round(min(1.0, len(words) / 50), 3)

    def _eval_groundedness(self, response: str, context: str) -> float:
        """Score groundedness by checking response terms against context."""
        if not context:
            return None
        context_words = set(context.lower().split())
        response_words = set(response.lower().split())
        stop_words = {"the", "a", "an", "is", "are", "and", "or", "but"}
        response_content = response_words - stop_words
        if not response_content:
            return 0.5
        grounded = len(response_content & context_words) / len(response_content)
        return round(min(1.0, grounded * 2), 3)
