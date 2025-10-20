"""
Basic Usage Example for ACE Framework
"""
import asyncio
import os
from ace import ACE
from ace.config_loader import get_ace_config


async def basic_example():
    """Basic example of using ACE framework"""
    
    # Load configuration from file
    try:
        config = get_ace_config()
        print("✅ Using configuration from config.yaml")
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        print("⚠️  Make sure config.yaml exists and is properly formatted")
        return
    
    # Initialize ACE
    ace = ACE(config)
    
    print("=== ACE Framework Basic Example ===\n")
    
    # Example 1: Solve a single query
    print("1. Solving a single query:")
    query = "Write a Python function to calculate the factorial of a number"
    
    trajectory, reflection = await ace.solve_query(query)
    
    print(f"Query: {query}")
    print(f"Success: {trajectory.success}")
    print(f"Execution Result: {trajectory.execution_result}")
    if trajectory.error_message:
        print(f"Error: {trajectory.error_message}")
    print()
    
    # Example 2: Offline adaptation with training data
    print("2. Performing offline adaptation:")
    
    training_queries = [
        "Write a function to check if a number is prime",
        "Create a function to find the maximum element in a list",
        "Write a function to reverse a string",
        "Create a function to calculate Fibonacci numbers"
    ]
    
    # Perform offline adaptation
    training_stats = await ace.offline_adaptation(training_queries, epochs=1)
    
    print(f"Training completed with {training_stats['epochs_completed']} epochs")
    print(f"Final playbook size: {training_stats['final_playbook_size']} bullets")
    print()
    
    # Example 3: Online adaptation
    print("3. Performing online adaptation:")
    
    new_query = "Write a function to sort a list of numbers"
    trajectory, reflection = await ace.online_adaptation(new_query)
    
    print(f"Query: {new_query}")
    print(f"Success: {trajectory.success}")
    print(f"Execution Result: {trajectory.execution_result}")
    print()
    
    # Example 4: Check playbook summary
    print("4. Playbook Summary:")
    summary = ace.get_playbook_summary()
    print(f"Total bullets: {summary['total_bullets']}")
    print(f"Sections: {list(summary['sections'].keys())}")
    print(f"Bullet types: {list(summary['bullet_types'].keys())}")
    print()
    
    # Example 5: Evaluate performance
    print("5. Performance Evaluation:")
    
    test_queries = [
        "Write a function to calculate the sum of two numbers",
        "Create a function to check if a string is a palindrome"
    ]
    
    eval_results = await ace.evaluate_performance(test_queries)
    print(f"Success rate: {eval_results['success_rate']:.2%}")
    print(f"Average confidence: {eval_results['average_confidence']:.2f}")
    print()
    
    # Example 6: Save and load playbook
    print("6. Save and Load Playbook:")
    ace.save_playbook("example_playbook.json")
    print("Playbook saved")
    
    # Create new ACE instance and load playbook
    ace2 = ACE(config)
    ace2.load_playbook("example_playbook.json")
    print("Playbook loaded into new instance")
    
    # Show statistics
    print("\n=== Final Statistics ===")
    stats = ace.get_statistics()
    for key, value in stats.items():
        print(f"{key}: {value}")


async def mathematical_reasoning_example():
    """Example focused on mathematical reasoning"""
    
    # Load configuration from file
    try:
        config = get_ace_config()
        print("✅ Using configuration from config.yaml")
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return
    
    ace = ACE(config)
    
    print("=== Mathematical Reasoning Example ===\n")
    
    # Training data for mathematical problems
    math_queries = [
        "Calculate the area of a circle with radius 5",
        "Find the derivative of x^2 + 3x + 2",
        "Solve the equation 2x + 5 = 15",
        "Calculate the sum of the first 10 natural numbers",
        "Find the probability of rolling a 6 on a fair die"
    ]
    
    print("Training on mathematical problems...")
    training_stats = await ace.offline_adaptation(math_queries, epochs=2)
    
    print(f"Training completed. Playbook size: {training_stats['final_playbook_size']}")
    
    # Test on new math problems
    test_math = [
        "Calculate the volume of a sphere with radius 3",
        "Find the integral of 2x dx",
        "Solve the equation x^2 - 4 = 0"
    ]
    
    print("\nTesting on new mathematical problems...")
    eval_results = await ace.evaluate_performance(test_math)
    print(f"Test success rate: {eval_results['success_rate']:.2%}")
    
    # Show playbook content
    print("\nPlaybook sections:")
    summary = ace.get_playbook_summary()
    for section, count in summary['sections'].items():
        print(f"  {section}: {count} bullets")


async def code_generation_example():
    """Example focused on code generation"""
    
    # Load configuration from file
    try:
        config = get_ace_config()
        print("✅ Using configuration from config.yaml")
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return
    
    ace = ACE(config)
    
    print("=== Code Generation Example ===\n")
    
    # Code generation training
    code_queries = [
        "Write a Python class for a stack data structure",
        "Create a function to read a CSV file",
        "Write a decorator to measure function execution time",
        "Create a function to validate email addresses",
        "Write a class to represent a bank account"
    ]
    
    print("Training on code generation tasks...")
    training_stats = await ace.offline_adaptation(code_queries, epochs=2)
    
    # Test on new coding tasks
    test_code = [
        "Write a function to generate random passwords",
        "Create a class for a binary tree node"
    ]
    
    print("\nTesting on new coding tasks...")
    eval_results = await ace.evaluate_performance(test_code)
    
    for i, result in enumerate(eval_results['query_results']):
        print(f"\nTest {i+1}: {result['query']}")
        print(f"Success: {result['success']}")
        print(f"Confidence: {result['confidence']:.2f}")
        if result['execution_result']:
            print(f"Result: {result['execution_result'][:100]}...")


if __name__ == "__main__":
    # Check if API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("Please set your OPENAI_API_KEY environment variable to run these examples.")
        print("You can get an API key from: https://platform.openai.com/")
        exit(1)
    
    print("Running ACE Framework Examples...\n")
    
    # Run examples
    asyncio.run(basic_example())
    print("\n" + "="*50 + "\n")
    asyncio.run(mathematical_reasoning_example())
    print("\n" + "="*50 + "\n")
    asyncio.run(code_generation_example())
    
    print("\nAll examples completed!")
