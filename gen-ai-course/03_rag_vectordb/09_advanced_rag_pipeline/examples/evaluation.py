"""
RAG Evaluation and Observability Example
Using RAGAS, Langfuse, and DeepEval
"""

from typing import List, Dict
from dataclasses import dataclass

try:
    from ragas import evaluate
    from ragas.metrics import (
        faithfulness,
        answer_relevance,
        context_precision,
        context_recall
    )
    from datasets import Dataset
    from langfuse import Langfuse
except ImportError:
    pass


@dataclass
class EvaluationResult:
    """Evaluation result container"""
    metric: str
    score: float
    threshold: float
    passed: bool


class RAGEvaluator:
    """RAG system evaluation with multiple metrics"""
    
    def __init__(self):
        self.metrics = {
            "faithfulness": faithfulness,
            "answer_relevance": answer_relevance,
            "context_precision": context_precision,
            "context_recall": context_recall
        }
    
    def prepare_dataset(self, test_cases: List[Dict]) -> Dataset:
        """Prepare dataset for RAGAS evaluation"""
        return Dataset.from_list(test_cases)
    
    def evaluate(self, test_cases: List[Dict]) -> Dict:
        """Run RAGAS evaluation"""
        dataset = self.prepare_dataset(test_cases)
        
        results = {}
        for name, metric in self.metrics.items():
            try:
                score = evaluate(dataset, metrics=[metric])
                results[name] = score
            except Exception as e:
                results[name] = {"error": str(e)}
        
        return results
    
    def generate_report(self, results: Dict) -> str:
        """Generate human-readable evaluation report"""
        report = ["RAG Evaluation Report", "=" * 30]
        
        for metric, data in results.items():
            if isinstance(data, dict) and "error" not in data:
                report.append(f"{metric}: {data.get('score', 'N/A'):.3f}")
            else:
                report.append(f"{metric}: Error - {data.get('error', 'Unknown')}")
        
        return "\n".join(report)


class ObservabilitySetup:
    """Set up observability with Langfuse"""
    
    def __init__(self, public_key: str = None, secret_key: str = None):
        if public_key and secret_key:
            self.langfuse = Langfuse(public_key=public_key, secret_key=secret_key)
        else:
            self.langfuse = None
    
    def create_trace(self, name: str, session_id: str = None):
        """Create a trace for Langfuse"""
        if self.langfuse:
            return self.langfuse.trace(name=name, session_id=session_id)
        return None
    
    def log_query(self, trace, query: str, response: str, 
                  context: List[str] = None, metrics: Dict = None):
        """Log query and response"""
        if not trace:
            return
        
        span = trace.span(
            name="rag-query",
            input=query,
            output=response,
            metadata=metrics or {}
        )
        
        if context:
            span.update(metadata={"context_chunks": len(context)})


class DeepEvalIntegration:
    """DeepEval for LLM evaluation"""
    
    def __init__(self):
        try:
            from deepeval import evaluate as deepeval_evaluate
            from deepeval.test_case import LLMTestCase
            from deepeval.metrics import AnswerRelevancyMetric
            
            self.deepeval_evaluate = deepeval_evaluate
            self.LLMTestCase = LLMTestCase
            self.AnswerRelevancyMetric = AnswerRelevancyMetric
        except ImportError:
            pass
    
    def run_test(self, question: str, answer: str, context: List[str]) -> Dict:
        """Run a single test case"""
        test_case = self.LLMTestCase(
            input=question,
            actual_output=answer,
            retrieval_context=context
        )
        
        metric = self.AnswerRelevancyMetric()
        score = metric.measure(test_case)
        
        return {
            "score": score,
            "success": score > 0.8,
            "reason": metric.reason
        }


class CustomMetrics:
    """Custom evaluation metrics"""
    
    @staticmethod
    def token_efficiency(question: str, context: List[str], answer: str) -> float:
        """Calculate token efficiency ratio"""
        context_tokens = sum(len(c.split()) for c in context)
        answer_tokens = len(answer.split())
        
        if answer_tokens == 0:
            return 0
        
        return context_tokens / answer_tokens
    
    @staticmethod
    def citation_accuracy(answer: str, sources: List[Dict]) -> float:
        """Check if citations are present and accurate"""
        import re
        
        # Find citation patterns like [1], [2]
        citations = re.findall(r'\[\d+\]', answer)
        
        if not citations:
            return 0.0
        
        # Check if cited sources are valid
        cited_nums = [int(c[1:-1]) for c in citations]
        valid_citations = sum(1 for num in cited_nums if num <= len(sources))
        
        return valid_citations / len(citations) if citations else 0
    
    @staticmethod
    def hallucination_score(answer: str, context: List[str]) -> float:
        """Simple hallucination detection"""
        # In production, use more sophisticated methods
        answer_lower = answer.lower()
        context_lower = " ".join(context).lower()
        
        # Check for specific claims in answer that aren't in context
        # This is a simplified heuristic
        return 0.0  # Placeholder


def run_evaluation():
    """Run complete evaluation pipeline"""
    evaluator = RAGEvaluator()
    
    test_cases = [
        {
            "question": "What is RAG?",
            "contexts": ["RAG stands for Retrieval-Augmented Generation..."],
            "answer": "RAG is a technique that combines retrieval with generation...",
            "ground_truth": "RAG combines retrieval and generation..."
        }
    ]
    
    results = evaluator.evaluate(test_cases)
    report = evaluator.generate_report(results)
    print(report)


if __name__ == "__main__":
    run_evaluation()