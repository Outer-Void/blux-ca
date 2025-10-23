"""FastAPI service for BLUX-cA."""

from __future__ import annotations

from fastapi import FastAPI

from ..core.constitution import ConstitutionEngine
from ..core.discernment import DiscernmentCompass
from ..core.perception import PerceptionLayer
from ..core.reflection import ReflectionEngine
from .schemas import ReflectRequest, ReflectResponse, VerdictResponse


class ConsciousAgentService:
    """Factory for FastAPI application exposing the cA capabilities."""

    def __init__(self) -> None:
        self.perception = PerceptionLayer()
        self.reflection = ReflectionEngine()
        self.compass = DiscernmentCompass()
        self.constitution = ConstitutionEngine()

    def create_app(self) -> FastAPI:
        app = FastAPI(title="BLUX-cA", version="0.1.0")

        @app.post("/reflect", response_model=ReflectResponse)
        def reflect(payload: ReflectRequest) -> ReflectResponse:
            observed = self.perception.observe(payload.text)
            insight = self.reflection.reflect(observed.text, seeds=["Initial observation"])
            return ReflectResponse(summary=insight.summary, chain=insight.chain)

        @app.post("/verdict", response_model=VerdictResponse)
        def verdict(payload: ReflectRequest) -> VerdictResponse:
            intent = self.compass.classify(payload.text)
            insight = self.reflection.reflect(payload.text, seeds=["Policy alignment"])
            decision = self.constitution.evaluate(
                insights=insight.chain, intent=intent.intent.value
            )
            return VerdictResponse(**decision.__dict__)

        return app


__all__ = ["ConsciousAgentService"]
