#!/usr/bin/env python3
"""
Quick script to run ACE framework examples
"""
import asyncio
import sys
import os

def check_config():
    """Check if configuration is available"""
    try:
        from ace.config_loader import get_ace_config
        config = get_ace_config()
        print("✅ Configuration loaded successfully")
        
        # Show provider info
        provider_type = getattr(config, 'provider_type', 'openai')
        print(f"📡 Using provider: {provider_type}")
        
        return True
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        print("\nPlease make sure config.yaml exists and is properly formatted")
        print("Or set OPENAI_API_KEY environment variable for OpenAI")
        return False

async def run_basic_example():
    """Run basic example"""
    print("🚀 Running Basic ACE Example")
    print("=" * 40)
    
    try:
        from examples.basic_usage import basic_example
        await basic_example()
    except Exception as e:
        print(f"❌ Error running basic example: {e}")

async def run_math_example():
    """Run mathematical reasoning example"""
    print("🔢 Running Mathematical Reasoning Example")
    print("=" * 40)
    
    try:
        from examples.basic_usage import mathematical_reasoning_example
        await mathematical_reasoning_example()
    except Exception as e:
        print(f"❌ Error running math example: {e}")

async def run_code_example():
    """Run code generation example"""
    print("💻 Running Code Generation Example")
    print("=" * 40)
    
    try:
        from examples.basic_usage import code_generation_example
        await code_generation_example()
    except Exception as e:
        print(f"❌ Error running code example: {e}")

async def run_demo():
    """Run a quick demo"""
    print("🎯 Quick ACE Demo")
    print("=" * 30)
    
    try:
        from ace import ACE, ACEConfig
        
        config = ACEConfig(
            generator_model="gpt-3.5-turbo",
            reflector_model="gpt-3.5-turbo",
            curator_model="gpt-3.5-turbo",
            max_reflector_rounds=1,
            max_epochs=1,
            max_playbook_bullets=10
        )
        
        ace = ACE(config)
        
        # Simple test
        query = "Write a hello world function in Python"
        trajectory, reflection = await ace.solve_query(query)
        
        print(f"Query: {query}")
        print(f"Success: {trajectory.success}")
        if trajectory.generated_code:
            print(f"Code:\n{trajectory.generated_code}")
        
        print(f"\n📚 Playbook size: {len(ace.playbook.bullets)} bullets")
        
    except Exception as e:
        print(f"❌ Error in demo: {e}")

def print_help():
    """Print help information"""
    print("""
ACE Framework Runner

Usage: python run_example.py [option]

Options:
  demo     - Run quick demo (default)
  basic    - Run basic usage examples
  math     - Run mathematical reasoning examples
  code     - Run code generation examples
  help     - Show this help message

Environment:
  Set OPENAI_API_KEY environment variable before running

Examples:
  export OPENAI_API_KEY='your-key'
  python run_example.py demo
  python run_example.py basic
""")

async def main():
    """Main function"""
    if not check_config():
        sys.exit(1)
    
    # Parse command line arguments
    option = sys.argv[1] if len(sys.argv) > 1 else "demo"
    
    if option == "help":
        print_help()
        return
    elif option == "basic":
        await run_basic_example()
    elif option == "math":
        await run_math_example()
    elif option == "code":
        await run_code_example()
    elif option == "demo":
        await run_demo()
    else:
        print(f"❌ Unknown option: {option}")
        print_help()
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
