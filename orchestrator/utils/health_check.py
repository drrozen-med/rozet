#!/usr/bin/env python3
"""Health check script for Rozet orchestrator.

Checks system configuration and reports status.
"""

import os
import sys
from pathlib import Path

def check_api_keys():
    """Check if API keys are configured."""
    openrouter = os.environ.get('OPENROUTER_API_KEY')
    openai = os.environ.get('OPENAI_API_KEY')
    
    if openrouter or openai:
        print('✅ API Keys: OK')
        return True
    else:
        print('❌ API Keys: ERROR - No OPENROUTER_API_KEY or OPENAI_API_KEY set')
        return False

def check_providers_yaml():
    """Check if providers.yaml exists and is valid."""
    config_path = Path('config/providers.yaml')
    
    if not config_path.exists():
        print('❌ Config File: ERROR - config/providers.yaml not found')
        return False
    
    try:
        import yaml
        with config_path.open() as f:
            yaml.safe_load(f)
        print('✅ Config File: OK')
        return True
    except Exception as e:
        print(f'❌ Config File: ERROR - Invalid YAML: {e}')
        return False

def check_config_loading():
    """Test if orchestrator can load configuration."""
    try:
        # Add project root to path
        project_root = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(project_root))
        from orchestrator.config_loader import load_provider_config
        config = load_provider_config()
        print(f'✅ Config Loading: OK (provider: {config.orchestrator.provider})')
        return True
    except Exception as e:
        print(f'❌ Config Loading: ERROR - {e}')
        return False

def main():
    """Run all health checks."""
    print('Rozet Orchestrator Health Check\n')
    
    checks = [
        check_api_keys,
        check_providers_yaml,
        check_config_loading,
    ]
    
    results = [check() for check in checks]
    
    print()
    if all(results):
        print('✅ All checks passed!')
        return 0
    else:
        print('❌ Some checks failed')
        return 1

if __name__ == '__main__':
    sys.exit(main())
