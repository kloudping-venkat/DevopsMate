"""
Check subcommand - run a specific check/collector.
Similar to Datadog's check command.
"""

import sys
import json
from typing import Optional


def cmd_check(args) -> None:
    """Run a specific check/collector."""
    from agent.internal.core.check_runner import CheckRunner
    from agent.pkg.config.loader import load_config
    
    # Load config
    config = load_config(args.config) if args.config else None
    
    # Create check runner
    runner = CheckRunner(config)
    
    # List available checks
    if args.list:
        checks = runner.list_checks()
        if args.json:
            print(json.dumps({"checks": checks}, indent=2))
        else:
            print("=== Available Checks ===")
            for check in checks:
                print(f"  - {check}")
        return
    
    # Run specific check
    if not args.check_name:
        print("Error: --check-name is required (use --list to see available checks)")
        sys.exit(1)
    
    try:
        result = runner.run_check(args.check_name, args.instance or None)
        
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            print(f"=== Running Check: {args.check_name} ===")
            if result.get('status') == 'ok':
                print("Status: ✓ OK")
            else:
                print(f"Status: ✗ {result.get('status', 'ERROR')}")
            
            if result.get('metrics'):
                print(f"\nMetrics collected: {len(result['metrics'])}")
                if args.verbose:
                    for metric in result['metrics'][:10]:  # Show first 10
                        print(f"  - {metric.get('name', 'unknown')}: {metric.get('value', 'N/A')}")
            
            if result.get('errors'):
                print("\nErrors:")
                for error in result['errors']:
                    print(f"  - {error}")
        
        sys.exit(0 if result.get('status') == 'ok' else 1)
        
    except Exception as e:
        print(f"Error running check: {e}")
        sys.exit(1)
