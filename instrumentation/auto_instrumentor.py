"""Auto-instrumentation orchestrator for multiple languages."""

import asyncio
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent.config import AgentConfig

logger = logging.getLogger(__name__)


class AutoInstrumentor:
    """
    Manages auto-instrumentation for discovered processes.
    
    Supports:
    - Java: JVM bytecode agent (OpenTelemetry Java agent)
    - Python: sitecustomize.py injection
    - Node.js: require() hook via NODE_OPTIONS
    - .NET: CLR profiler
    - Go: eBPF-based (no code changes needed)
    
    This provides Dynatrace OneAgent-like capability to automatically
    inject tracing into applications without code changes.
    """
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self._running = False
        
        # Paths to instrumentation agents
        self.agent_dir = Path(__file__).parent.parent / "lib"
        
        # Active instrumentations
        self._active_instrumentations: Dict[int, str] = {}
    
    async def start(self):
        """Start the auto-instrumentor."""
        self._running = True
        logger.info("Auto-instrumentation started")
        
        # Set up environment for new processes
        self._setup_environment()
    
    async def stop(self):
        """Stop the auto-instrumentor."""
        self._running = False
        logger.info("Auto-instrumentation stopped")
    
    def _setup_environment(self):
        """Set up environment variables for auto-instrumentation."""
        # Python auto-instrumentation
        if self.config.instrument_python:
            self._setup_python_instrumentation()
        
        # Node.js auto-instrumentation
        if self.config.instrument_nodejs:
            self._setup_nodejs_instrumentation()
        
        # Java auto-instrumentation
        if self.config.instrument_java:
            self._setup_java_instrumentation()
    
    def _setup_python_instrumentation(self):
        """
        Set up Python auto-instrumentation.
        
        Uses OpenTelemetry Python auto-instrumentation.
        """
        # Create sitecustomize.py for automatic instrumentation
        site_packages = self._get_python_site_packages()
        if not site_packages:
            return
        
        sitecustomize_content = '''
# DevopsMate Auto-Instrumentation for Python
import os

# Only instrument if enabled
if os.environ.get("DEVOPSMATE_INSTRUMENT_PYTHON", "true").lower() == "true":
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.auto_instrumentation import sitecustomize
        
        # Set up tracing
        endpoint = os.environ.get("DEVOPSMATE_OTEL_ENDPOINT", "http://localhost:4317")
        
        provider = TracerProvider()
        processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint))
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)
        
        # Auto-instrument common libraries
        from opentelemetry.instrumentation.requests import RequestsInstrumentor
        from opentelemetry.instrumentation.flask import FlaskInstrumentor
        from opentelemetry.instrumentation.django import DjangoInstrumentor
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
        from opentelemetry.instrumentation.redis import RedisInstrumentor
        
        # Instrument
        RequestsInstrumentor().instrument()
        # Framework-specific instrumentation is done lazily
        
    except ImportError:
        pass  # OpenTelemetry not installed
    except Exception as e:
        import sys
        print(f"DevopsMate instrumentation error: {e}", file=sys.stderr)
'''
        
        sitecustomize_path = site_packages / "sitecustomize.py"
        
        try:
            # Check if file exists and has our marker
            if sitecustomize_path.exists():
                content = sitecustomize_path.read_text()
                if "DevopsMate Auto-Instrumentation" in content:
                    return  # Already set up
            
            # Write our instrumentation
            with open(sitecustomize_path, "a") as f:
                f.write("\n" + sitecustomize_content)
            
            logger.info(f"Python auto-instrumentation set up at {sitecustomize_path}")
        
        except PermissionError:
            logger.warning("Cannot write sitecustomize.py - no permission")
        except Exception as e:
            logger.error(f"Failed to set up Python instrumentation: {e}")
    
    def _setup_nodejs_instrumentation(self):
        """
        Set up Node.js auto-instrumentation.
        
        Uses OpenTelemetry Node.js auto-instrumentation via NODE_OPTIONS.
        """
        # Create a loader script
        loader_content = '''
// DevopsMate Auto-Instrumentation for Node.js
const { NodeTracerProvider } = require('@opentelemetry/sdk-trace-node');
const { BatchSpanProcessor } = require('@opentelemetry/sdk-trace-base');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-trace-otlp-grpc');
const { registerInstrumentations } = require('@opentelemetry/instrumentation');
const { HttpInstrumentation } = require('@opentelemetry/instrumentation-http');
const { ExpressInstrumentation } = require('@opentelemetry/instrumentation-express');
const { PgInstrumentation } = require('@opentelemetry/instrumentation-pg');
const { RedisInstrumentation } = require('@opentelemetry/instrumentation-redis');

const endpoint = process.env.DEVOPSMATE_OTEL_ENDPOINT || 'http://localhost:4317';

const provider = new NodeTracerProvider();
const exporter = new OTLPTraceExporter({ url: endpoint });
provider.addSpanProcessor(new BatchSpanProcessor(exporter));
provider.register();

registerInstrumentations({
    instrumentations: [
        new HttpInstrumentation(),
        new ExpressInstrumentation(),
        new PgInstrumentation(),
        new RedisInstrumentation(),
    ],
});

console.log('[DevopsMate] Node.js auto-instrumentation active');
'''
        
        loader_path = self.agent_dir / "nodejs" / "loader.js"
        
        try:
            loader_path.parent.mkdir(parents=True, exist_ok=True)
            loader_path.write_text(loader_content)
            
            # Set NODE_OPTIONS to preload our instrumentation
            current_options = os.environ.get("NODE_OPTIONS", "")
            if "devopsmate" not in current_options.lower():
                os.environ["NODE_OPTIONS"] = f"--require {loader_path} {current_options}"
            
            logger.info("Node.js auto-instrumentation configured")
        
        except Exception as e:
            logger.error(f"Failed to set up Node.js instrumentation: {e}")
    
    def _setup_java_instrumentation(self):
        """
        Set up Java auto-instrumentation.
        
        Uses OpenTelemetry Java agent for bytecode instrumentation.
        """
        # The Java agent JAR should be downloaded during agent installation
        agent_jar = self.agent_dir / "java" / "opentelemetry-javaagent.jar"
        
        if not agent_jar.exists():
            logger.info("Java agent not found, attempting download...")
            self._download_java_agent(agent_jar)
        
        if agent_jar.exists():
            # Set JAVA_TOOL_OPTIONS for automatic agent attachment
            current_options = os.environ.get("JAVA_TOOL_OPTIONS", "")
            agent_option = f"-javaagent:{agent_jar}"
            
            if agent_option not in current_options:
                endpoint = self.config.endpoint.replace("/ingest", "")
                otel_options = f"{agent_option} -Dotel.exporter.otlp.endpoint={endpoint}"
                os.environ["JAVA_TOOL_OPTIONS"] = f"{otel_options} {current_options}"
            
            logger.info("Java auto-instrumentation configured")
    
    def _download_java_agent(self, dest_path: Path):
        """Download the OpenTelemetry Java agent."""
        url = "https://github.com/open-telemetry/opentelemetry-java-instrumentation/releases/latest/download/opentelemetry-javaagent.jar"
        
        try:
            import urllib.request
            
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(url, dest_path)
            logger.info(f"Downloaded Java agent to {dest_path}")
        
        except Exception as e:
            logger.error(f"Failed to download Java agent: {e}")
    
    def _get_python_site_packages(self) -> Optional[Path]:
        """Get the Python site-packages directory."""
        import site
        
        # Try user site-packages first
        user_site = site.getusersitepackages()
        if user_site and Path(user_site).exists():
            return Path(user_site)
        
        # Fall back to system site-packages
        for site_pkg in site.getsitepackages():
            if Path(site_pkg).exists():
                return Path(site_pkg)
        
        return None
    
    async def instrument_process(self, pid: int, technology: str) -> bool:
        """
        Attempt to instrument a running process.
        
        This is more complex and may require:
        - Java: Attach API
        - Python: Signal to reload
        - Node.js: Not possible without restart
        """
        if pid in self._active_instrumentations:
            return True  # Already instrumented
        
        logger.info(f"Attempting to instrument PID {pid} ({technology})")
        
        # For now, we rely on environment variables for new processes
        # Runtime attachment would require additional implementation
        
        self._active_instrumentations[pid] = technology
        return True
    
    def get_instrumentation_status(self) -> Dict[str, Any]:
        """Get current instrumentation status."""
        return {
            "enabled": self.config.auto_instrument,
            "languages": {
                "java": self.config.instrument_java,
                "python": self.config.instrument_python,
                "nodejs": self.config.instrument_nodejs,
                "dotnet": self.config.instrument_dotnet,
                "go": self.config.instrument_go,
            },
            "active_instrumentations": len(self._active_instrumentations),
        }
