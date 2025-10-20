"""
ACE Framework - Main Entry Point
"""
import asyncio
import os
from ace import ACE
from ace.config_loader import get_ace_config


async def main():
    """Main function demonstrating ACE framework"""
    
    print("🚀 ACE Framework - Agentic Context Engineering")
    print("=" * 50)
    
    # Load configuration from file
    try:
        config = get_ace_config()
        print("✅ Configuration loaded from config.yaml")
        
        # Show provider info
        provider_type = getattr(config, 'provider_type', 'openai')
        print(f"📡 Using provider: {provider_type}")
        
        if provider_type == "custom":
            base_url = getattr(config, 'openai_base_url', 'Unknown')
            print(f"🔗 API endpoint: {base_url}")
        
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        print("⚠️  Using default configuration")
        
        # Fallback to basic config
        from ace import ACEConfig
        config = ACEConfig(
            generator_model="gpt-3.5-turbo",
            reflector_model="gpt-3.5-turbo",
            curator_model="gpt-3.5-turbo",
            max_reflector_rounds=2,
            max_epochs=2,
            max_playbook_bullets=50
        )
    
    # Initialize ACE
    ace = ACE(config)
    print("✅ ACE Framework initialized successfully")
    
    # Demonstrate basic functionality
    print("\n📝 Demonstrating ACE Framework...")
    
    # Example query
    query = "Write a Python function to calculate the factorial of a number"
    print(f"\n🔍 Solving query: {query}")
    
    try:
        trajectory, reflection = await ace.solve_query(query)
        
        print(f"✅ Success: {trajectory.success}")
        if trajectory.generated_code:
            print(f"💻 Generated code:\n{trajectory.generated_code}")
        
        if trajectory.error_message:
            print(f"❌ Error: {trajectory.error_message}")
        
        # Show playbook summary
        summary = ace.get_playbook_summary()
        print(f"\n📚 Playbook now contains {summary['total_bullets']} bullets")
        
        # Show statistics
        stats = ace.get_statistics()
        print(f"📊 Success rate: {stats['success_rate']:.2%}")
        
    except Exception as e:
        print(f"❌ Error during execution: {e}")
        print("💡 This might be due to API issues. Check your API key and connection.")
    
    print("\n🎉 ACE Framework demonstration completed!")
    print("\n📖 For more examples, see:")
    print("   - examples/basic_usage.py")
    print("   - Run tests with: python -m pytest tests/")


if __name__ == "__main__":
    asyncio.run(main())
