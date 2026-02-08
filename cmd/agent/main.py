"""
DevopsMate Agent - Main Entry Point

Similar to Datadog Agent's cmd/agent/main.go structure.
Provides CLI interface with subcommands: run, status, version, configcheck, etc.
"""

import asyncio
import sys
import argparse
import signal
from pathlib import Path
from typing import Optional
import logging

from agent.internal.core.agent import Agent
from agent.pkg.config.loader import load_config
from agent.pkg.version import get_version

logger = logging.getLogger(__name__)


def setup_logging(debug: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def cmd_run(args):
    """Run the agent (main command)."""
    from agent.internal.core.runner import AgentRunner
    
    setup_logging(args.debug)
    
    logger.info(f"Starting DevopsMate Agent {get_version()}")
    
    # Load configuration
    config = load_config(args.config)
    
    # Override with CLI args
    if args.endpoint:
        config.endpoint = args.endpoint
    if args.api_key:
        config.api_key = args.api_key
    if args.tenant_id:
        config.tenant_id = args.tenant_id
    
    # Create and run agent
    runner = AgentRunner(config)
    
    # Setup signal handlers
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    def shutdown_handler(signum=None, frame=None):
        logger.info("Received shutdown signal")
        loop.create_task(runner.stop())
    
    if sys.platform != "win32":
        signal.signal(signal.SIGTERM, shutdown_handler)
        signal.signal(signal.SIGINT, shutdown_handler)
    
    try:
        loop.run_until_complete(runner.start())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        loop.run_until_complete(runner.stop())
    finally:
        loop.close()


def cmd_status(args):
    """Show agent status."""
    from agent.internal.status.status import get_agent_status
    
    setup_logging(args.debug)
    status = get_agent_status()
    
    print("=== DevopsMate Agent Status ===")
    print(f"Version: {status.get('version', 'unknown')}")
    print(f"Status: {status.get('status', 'unknown')}")
    print(f"Uptime: {status.get('uptime', 'unknown')}")
    print(f"PID: {status.get('pid', 'unknown')}")
    
    if status.get('components'):
        print("\nComponents:")
        for comp_name, comp_status in status['components'].items():
            print(f"  {comp_name}: {comp_status}")


def cmd_version(args):
    """Show agent version."""
    version = get_version()
    print(f"DevopsMate Agent {version}")


def cmd_configcheck(args):
    """Validate configuration file."""
    from agent.pkg.config.validator import validate_config
    
    setup_logging(args.debug)
    
    config_path = args.config or "agent.yaml"
    
    if not Path(config_path).exists():
        print(f"Error: Config file not found: {config_path}")
        sys.exit(1)
    
    try:
        config = load_config(config_path)
        errors = validate_config(config)
        
        if errors:
            print("Configuration errors found:")
            for error in errors:
                print(f"  - {error}")
            sys.exit(1)
        else:
            print("Configuration is valid ✓")
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)


def cmd_flare(args):
    """Collect diagnostic information (similar to Datadog's agent flare)."""
    from agent.internal.diagnostics.flare import collect_flare
    
    setup_logging(args.debug)
    
    output_path = args.output or f"devopsmate-agent-flare-{int(asyncio.get_event_loop().time())}.tar.gz"
    
    print(f"Collecting diagnostic information...")
    flare_path = collect_flare(output_path)
    
    print(f"Flare collected: {flare_path}")
    print("Please share this file with support for troubleshooting.")


def cmd_health(args):
    """Check agent health."""
    from agent.internal.health.health import check_health
    
    setup_logging(args.debug)
    
    health = check_health()
    
    if health['healthy']:
        print("Agent is healthy ✓")
        sys.exit(0)
    else:
        print("Agent is unhealthy ✗")
        if health.get('errors'):
            for error in health['errors']:
                print(f"  - {error}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="DevopsMate Universal Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  devopsmate-agent run --config agent.yaml
  devopsmate-agent status
  devopsmate-agent version
  devopsmate-agent configcheck --config agent.yaml
  devopsmate-agent flare
  devopsmate-agent health
  devopsmate-agent diagnose
  devopsmate-agent integrations --list
  devopsmate-agent check --list
  devopsmate-agent check --check-name host_metrics
  devopsmate-agent hostname
        """
    )
    
    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="Enable debug logging"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # run command
    run_parser = subparsers.add_parser("run", help="Run the agent")
    run_parser.add_argument("--config", "-c", help="Path to config file")
    run_parser.add_argument("--endpoint", "-e", help="API endpoint")
    run_parser.add_argument("--api-key", "-k", help="API key")
    run_parser.add_argument("--tenant-id", "-t", help="Tenant ID")
    run_parser.set_defaults(func=cmd_run)
    
    # status command
    status_parser = subparsers.add_parser("status", help="Show agent status")
    status_parser.set_defaults(func=cmd_status)
    
    # version command
    version_parser = subparsers.add_parser("version", help="Show agent version")
    version_parser.set_defaults(func=cmd_version)
    
    # configcheck command
    configcheck_parser = subparsers.add_parser("configcheck", help="Validate configuration")
    configcheck_parser.add_argument("--config", "-c", help="Path to config file")
    configcheck_parser.set_defaults(func=cmd_configcheck)
    
    # flare command
    flare_parser = subparsers.add_parser("flare", help="Collect diagnostic information")
    flare_parser.add_argument("--output", "-o", help="Output file path")
    flare_parser.set_defaults(func=cmd_flare)
    
    # health command
    health_parser = subparsers.add_parser("health", help="Check agent health")
    health_parser.set_defaults(func=cmd_health)
    
    # diagnose command
    diagnose_parser = subparsers.add_parser("diagnose", help="Run comprehensive diagnostics")
    diagnose_parser.set_defaults(func=lambda args: __import__('agent.cmd.agent.subcommands.diagnose', fromlist=['cmd_diagnose']).cmd_diagnose(args))
    
    # integrations command
    integrations_parser = subparsers.add_parser("integrations", help="List available integrations")
    integrations_parser.add_argument("--json", action="store_true", help="Output as JSON")
    integrations_parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed information")
    integrations_parser.set_defaults(func=lambda args: __import__('agent.cmd.agent.subcommands.integrations', fromlist=['cmd_integrations']).cmd_integrations(args))
    
    # check command
    check_parser = subparsers.add_parser("check", help="Run a specific check/collector")
    check_parser.add_argument("--list", "-l", action="store_true", help="List available checks")
    check_parser.add_argument("--check-name", "-n", help="Name of check to run")
    check_parser.add_argument("--instance", "-i", help="Instance name (optional)")
    check_parser.add_argument("--config", "-c", help="Path to config file")
    check_parser.add_argument("--json", action="store_true", help="Output as JSON")
    check_parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    check_parser.set_defaults(func=lambda args: __import__('agent.cmd.agent.subcommands.check', fromlist=['cmd_check']).cmd_check(args))
    
    # hostname command
    hostname_parser = subparsers.add_parser("hostname", help="Show resolved hostname")
    hostname_parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed information")
    hostname_parser.set_defaults(func=lambda args: __import__('agent.cmd.agent.subcommands.hostname', fromlist=['cmd_hostname']).cmd_hostname(args))
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.exception("Fatal error")
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
