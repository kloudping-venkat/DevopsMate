"""
Diagnose subcommand - comprehensive diagnostics.
Similar to Datadog's diagnose command.
"""

import sys
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


def cmd_diagnose(args) -> None:
    """Run comprehensive diagnostics."""
    from agent.internal.diagnostics.diagnose import run_diagnostics
    
    results = run_diagnostics()
    
    print("=== DevopsMate Agent Diagnostics ===\n")
    
    # Print results
    for category, checks in results.items():
        print(f"\n{category}:")
        print("-" * 50)
        
        for check_name, check_result in checks.items():
            status = "✓" if check_result['status'] == 'ok' else "✗"
            print(f"  {status} {check_name}")
            
            if check_result.get('message'):
                print(f"      {check_result['message']}")
            
            if check_result.get('errors'):
                for error in check_result['errors']:
                    print(f"      ERROR: {error}")
    
    # Summary
    total = sum(len(checks) for checks in results.values())
    passed = sum(
        sum(1 for r in checks.values() if r['status'] == 'ok')
        for checks in results.values()
    )
    
    print(f"\n{'=' * 50}")
    print(f"Summary: {passed}/{total} checks passed")
    
    if passed < total:
        sys.exit(1)
    else:
        sys.exit(0)
