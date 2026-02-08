"""
Integrations subcommand - list available integrations.
Similar to Datadog's integrations command.
"""

import json
from typing import List, Dict, Any


def cmd_integrations(args) -> None:
    """List available integrations."""
    # Import from frontend data (or create agent-specific list)
    try:
        from frontend.src.data.integrations import integrations, categories
    except ImportError:
        # Fallback to basic list
        integrations = _get_basic_integrations()
        categories = list(set(i['category'] for i in integrations))
    
    if args.json:
        # JSON output
        output = {
            "integrations": integrations,
            "categories": categories,
            "total": len(integrations)
        }
        print(json.dumps(output, indent=2))
        return
    
    # Human-readable output
    print("=== DevopsMate Agent Integrations ===\n")
    print(f"Total: {len(integrations)} integrations\n")
    
    # Group by category
    by_category = {}
    for integration in integrations:
        cat = integration.get('category', 'Other')
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(integration)
    
    # Print by category
    for category in sorted(by_category.keys()):
        items = by_category[category]
        print(f"\n{category} ({len(items)}):")
        print("-" * 50)
        
        for item in sorted(items, key=lambda x: x.get('name', '')):
            name = item.get('name', 'Unknown')
            status = item.get('status', 'disconnected')
            status_icon = "●" if status == 'connected' else "○"
            print(f"  {status_icon} {name}")
            
            if args.verbose and item.get('description'):
                desc = item['description'][:60] + "..." if len(item.get('description', '')) > 60 else item.get('description', '')
                print(f"      {desc}")


def _get_basic_integrations() -> List[Dict[str, Any]]:
    """Get basic integrations list if frontend data not available."""
    return [
        {"name": "AWS", "category": "Cloud", "status": "disconnected"},
        {"name": "Azure", "category": "Cloud", "status": "disconnected"},
        {"name": "GCP", "category": "Cloud", "status": "disconnected"},
        {"name": "Docker", "category": "Infrastructure", "status": "disconnected"},
        {"name": "Kubernetes", "category": "Infrastructure", "status": "disconnected"},
        {"name": "PostgreSQL", "category": "Database", "status": "disconnected"},
        {"name": "MySQL", "category": "Database", "status": "disconnected"},
        {"name": "Redis", "category": "Database", "status": "disconnected"},
        {"name": "Prometheus", "category": "Monitoring", "status": "disconnected"},
        {"name": "Grafana", "category": "Monitoring", "status": "disconnected"},
    ]
