#!/usr/bin/env python3
"""Setup script to help users configure API keys for Rozet orchestrator."""

import os
import sys
from pathlib import Path

def check_env_file():
    """Check if .env file exists and has API keys."""
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    
    if not env_file.exists():
        print("❌ .env file not found")
        return False
    
    # Load .env if python-dotenv is available
    try:
        from dotenv import load_dotenv
        load_dotenv(env_file)
    except ImportError:
        print("⚠️  python-dotenv not installed, reading .env manually...")
        with env_file.open() as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    
    openrouter = os.environ.get('OPENROUTER_API_KEY', '').strip()
    openai = os.environ.get('OPENAI_API_KEY', '').strip()
    
    if not openrouter and not openai:
        print("❌ No API keys found in .env file")
        print("   Please set OPENROUTER_API_KEY or OPENAI_API_KEY")
        return False
    
    if openrouter and not openrouter.startswith('sk-'):
        print("⚠️  OPENROUTER_API_KEY found but doesn't look like a valid key")
    
    if openai and not openai.startswith('sk-'):
        print("⚠️  OPENAI_API_KEY found but doesn't look like a valid key")
    
    print("✅ API keys found in .env file")
    return True

def create_env_file():
    """Create .env file from .env.example if it doesn't exist."""
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    example_file = project_root / ".env.example"
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if example_file.exists():
        import shutil
        shutil.copy(example_file, env_file)
        print("✅ Created .env file from .env.example")
        print("   Please edit .env and add your API keys")
        return True
    else:
        print("❌ .env.example not found")
        return False

def test_config_loading():
    """Test if orchestrator can load configuration."""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from orchestrator.config_loader import load_provider_config
        config = load_provider_config()
        print(f"✅ Config loaded successfully")
        print(f"   Provider: {config.orchestrator.provider}")
        print(f"   Model: {config.orchestrator.model}")
        return True
    except Exception as e:
        print(f"❌ Config loading failed: {e}")
        return False

def test_api_connection():
    """Test if we can actually connect to the API."""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from orchestrator.config_loader import load_provider_config
        from orchestrator.providers.factory import create_chat_model
        from langchain_core.messages import HumanMessage
        
        config = load_provider_config()
        llm, _ = create_chat_model(config.orchestrator)
        
        print("   Testing API connection...")
        response = llm.invoke([HumanMessage(content="Say 'test'")])
        print(f"✅ API connection successful: {response.content[:50]}")
        return True
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return False

def main():
    """Run setup checks."""
    print("Rozet Orchestrator API Key Setup\n")
    print("=" * 50)
    
    # Check if .env exists
    if not check_env_file():
        print("\nCreating .env file...")
        create_env_file()
        print("\n⚠️  Please edit .env and add your API keys, then run this script again")
        return 1
    
    print("\nTesting configuration...")
    if not test_config_loading():
        return 1
    
    print("\nTesting API connection...")
    if not test_api_connection():
        print("\n⚠️  API connection failed. Please check:")
        print("   1. Your API key is correct in .env")
        print("   2. You have internet connection")
        print("   3. Your API key has sufficient credits")
        return 1
    
    print("\n" + "=" * 50)
    print("✅ All checks passed! Rozet is ready to use.")
    return 0

if __name__ == "__main__":
    sys.exit(main())

