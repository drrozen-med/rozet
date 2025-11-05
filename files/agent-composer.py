#!/usr/bin/env python3
"""
Agent Composer - Build custom agents from modular behavioral components

Usage:
    python agent-composer.py \\
        --template templates/local-coder-agent.md \\
        --behaviors anti-laziness,humility,verification \\
        --integrations mcp-devtools,bash-tool \\
        --output agents/my-agent.md
"""

import argparse
import json
import os
from pathlib import Path
from typing import List, Dict

class AgentComposer:
    def __init__(self, framework_root: str = "."):
        self.root = Path(framework_root)
        self.core_dir = self.root / "core"
        self.integrations_dir = self.root / "integrations"
        self.templates_dir = self.root / "templates"
        self.config_dir = self.root / "config"
        
    def load_config(self, config_file: str = "behavior-settings.json") -> Dict:
        """Load configuration from JSON file"""
        config_path = self.config_dir / config_file
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def load_module(self, module_path: Path) -> str:
        """Load a behavioral module"""
        with open(module_path, 'r') as f:
            return f.read()
    
    def load_template(self, template_name: str) -> str:
        """Load an agent template"""
        template_path = self.templates_dir / template_name
        with open(template_path, 'r') as f:
            return f.read()
    
    def get_available_behaviors(self) -> List[str]:
        """List all available behavioral modules"""
        if not self.core_dir.exists():
            return []
        return [f.stem for f in self.core_dir.glob("*.md")]
    
    def get_available_integrations(self) -> List[str]:
        """List all available integration modules"""
        if not self.integrations_dir.exists():
            return []
        return [f.stem for f in self.integrations_dir.glob("*.md")]
    
    def compose_agent(
        self,
        template: str,
        behaviors: List[str],
        integrations: List[str],
        config_override: Dict = None
    ) -> str:
        """Compose an agent from template and modules"""
        
        # Load base template
        agent_prompt = self.load_template(template)
        
        # Add a marker for module insertion
        modules_section = "\n\n## Behavioral Modules\n\n"
        
        # Load and add behavioral modules
        for behavior in behaviors:
            behavior_path = self.core_dir / f"{behavior}.md"
            if behavior_path.exists():
                module_content = self.load_module(behavior_path)
                modules_section += f"\n### {behavior.replace('-', ' ').title()}\n\n"
                modules_section += module_content + "\n\n---\n"
            else:
                print(f"Warning: Behavior module '{behavior}' not found")
        
        # Load and add integration modules
        if integrations:
            modules_section += "\n## Integration Modules\n\n"
            for integration in integrations:
                integration_path = self.integrations_dir / f"{integration}.md"
                if integration_path.exists():
                    module_content = self.load_module(integration_path)
                    modules_section += f"\n### {integration.replace('-', ' ').title()}\n\n"
                    modules_section += module_content + "\n\n---\n"
                else:
                    print(f"Warning: Integration module '{integration}' not found")
        
        # Load config
        config = self.load_config()
        
        # Apply config override if provided
        if config_override:
            config.update(config_override)
        
        # Add config section
        config_section = "\n\n## Configuration\n\n```json\n"
        config_section += json.dumps(config, indent=2)
        config_section += "\n```\n"
        
        # Combine everything
        final_prompt = agent_prompt + modules_section + config_section
        
        return final_prompt
    
    def save_agent(self, content: str, output_path: str):
        """Save composed agent to file"""
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output, 'w') as f:
            f.write(content)
        
        print(f"✓ Agent saved to: {output_path}")

def main():
    parser = argparse.ArgumentParser(
        description="Compose AI agents from modular behavioral components"
    )
    
    parser.add_argument(
        "--template",
        required=True,
        help="Agent template file (e.g., templates/local-coder-agent.md)"
    )
    
    parser.add_argument(
        "--behaviors",
        default="",
        help="Comma-separated list of behavioral modules (e.g., anti-laziness,humility)"
    )
    
    parser.add_argument(
        "--integrations",
        default="",
        help="Comma-separated list of integration modules (e.g., mcp-devtools,bash-tool)"
    )
    
    parser.add_argument(
        "--config-override",
        default="{}",
        help="JSON string to override config settings"
    )
    
    parser.add_argument(
        "--output",
        required=True,
        help="Output file path for composed agent"
    )
    
    parser.add_argument(
        "--list-behaviors",
        action="store_true",
        help="List available behavioral modules"
    )
    
    parser.add_argument(
        "--list-integrations",
        action="store_true",
        help="List available integration modules"
    )
    
    parser.add_argument(
        "--framework-root",
        default=".",
        help="Root directory of behavioral framework (default: current directory)"
    )
    
    args = parser.parse_args()
    
    composer = AgentComposer(args.framework_root)
    
    # List behaviors if requested
    if args.list_behaviors:
        behaviors = composer.get_available_behaviors()
        print("Available behavioral modules:")
        for b in behaviors:
            print(f"  - {b}")
        return
    
    # List integrations if requested
    if args.list_integrations:
        integrations = composer.get_available_integrations()
        print("Available integration modules:")
        for i in integrations:
            print(f"  - {i}")
        return
    
    # Parse behaviors and integrations
    behaviors = [b.strip() for b in args.behaviors.split(",") if b.strip()]
    integrations = [i.strip() for i in args.integrations.split(",") if i.strip()]
    
    # Parse config override
    config_override = json.loads(args.config_override)
    
    # Compose agent
    print(f"Composing agent from template: {args.template}")
    print(f"Behaviors: {behaviors}")
    print(f"Integrations: {integrations}")
    
    agent_content = composer.compose_agent(
        template=args.template,
        behaviors=behaviors,
        integrations=integrations,
        config_override=config_override
    )
    
    # Save agent
    composer.save_agent(agent_content, args.output)
    
    print(f"\n✓ Agent composition complete!")
    print(f"  - Total length: {len(agent_content)} characters")
    print(f"  - Modules included: {len(behaviors) + len(integrations)}")

if __name__ == "__main__":
    main()
