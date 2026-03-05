"""Bartender Journal API — application entry point."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.admin import setup_admin
from app.constants import OTEL_SERVICE_NAME
from app.metrics import instrumentator
from app.middleware import add_app_header
from app.routes import auth, comments, health, library, posts
from app.settings import settings

app = FastAPI(title=settings.app_name)

# --- Prometheus auto-instrumentation ---
instrumentator.instrument(app).expose(app)

# --- OpenTelemetry ---
resource = Resource.create({"service.name": OTEL_SERVICE_NAME})
trace_provider = TracerProvider(resource=resource)
trace_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
trace.set_tracer_provider(trace_provider)
FastAPIInstrumentor.instrument_app(app, tracer_provider=trace_provider)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Admin panel ---
setup_admin(app)

# --- Routes ---
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(posts.router)
app.include_router(comments.router)
app.include_router(library.router)

# --- Custom middleware ---
app.middleware("http")(add_app_header)
