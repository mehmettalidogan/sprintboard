"""
Mock NLP Service — simulates calculating task complexity.
"""
from __future__ import annotations

import random

class NLPMockService:
    """
    Mock service to generate a random complexity score (1.0 - 5.0)
    for a given task based on its title and description.
    """

    async def calculate_task_complexity(self, title: str, description: str | None) -> float:
        """
        Returns a random float between 1.0 and 5.0 representing task complexity.
        """
        # Normally this would call an LLM or use an ML model.
        # We round to 2 decimal places for neatness.
        return round(random.uniform(1.0, 5.0), 2)
