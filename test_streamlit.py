#!/usr/bin/env python3
"""
Test script for ACE Framework Streamlit Application
Validates all components and functionality
"""
import sys
import os
import asyncio
import tempfile
import json
from pathlib import Path
import datetime

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all required imports work"""
    print("🔍 Testing imports...")

    try:
        import streamlit as st
        print("✅ streamlit imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import streamlit: {e}")
        return False

    try:
        import plotly
        print("✅ plotly imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import plotly: {e}")
        return False

    try:
        import networkx
        print("✅ networkx imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import networkx: {e}")
        return False

    try:
        import pandas
        print("✅ pandas imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import pandas: {e}")
        return False

    try:
        from ace import ACE, ACEConfig, Playbook, Bullet, BulletType, BulletTag
        print("✅ ACE framework imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import ACE framework: {e}")
        return False

    try:
        from ace.streamlit_utils import (
            create_bullet_network_visualization,
            create_trajectory_timeline,
            create_playbook_evolution_chart,
            create_bullet_type_distribution,
            create_performance_metrics,
            create_query_analysis_dashboard,
            display_trajectory_details,
            display_reflection_details,
            export_session_data,
            create_bullet_heatmap
        )
        print("✅ Streamlit utilities imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import streamlit utilities: {e}")
        return False

    return True

def test_ace_initialization():
    """Test ACE framework initialization"""
    print("\n🔍 Testing ACE framework initialization...")

    try:
        from ace.config_loader import get_ace_config
        config = get_ace_config()
        print("✅ Configuration loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        return False

    try:
        from ace import ACE
        ace = ACE(config)
        print("✅ ACE framework initialized successfully")
        return ace
    except Exception as e:
        print(f"❌ Failed to initialize ACE framework: {e}")
        return False

def test_playbook_creation():
    """Test playbook creation and management"""
    print("\n🔍 Testing playbook creation...")

    try:
        from ace import Playbook, Bullet, BulletType

        # Create test bullets
        bullets = [
            Bullet(
                content="Test strategy bullet",
                bullet_type=BulletType.STRATEGY,
                section="test_section"
            ),
            Bullet(
                content="Test error pattern",
                bullet_type=BulletType.ERROR_PATTERN,
                section="test_section"
            ),
            Bullet(
                content="Test API guideline",
                bullet_type=BulletType.API_GUIDELINE,
                section="api_section"
            )
        ]

        # Create playbook
        playbook = Playbook()
        for bullet in bullets:
            playbook.add_bullet(bullet)

        print(f"✅ Created playbook with {len(playbook.bullets)} bullets")
        return playbook

    except Exception as e:
        print(f"❌ Failed to create playbook: {e}")
        return None

def test_visualizations():
    """Test visualization functions"""
    print("\n🔍 Testing visualizations...")

    try:
        from ace.streamlit_utils import (
            create_bullet_network_visualization,
            create_bullet_type_distribution,
            create_bullet_heatmap
        )

        # Create test playbook
        from ace import Playbook, Bullet, BulletType
        bullets = [
            Bullet(content="Test bullet 1", bullet_type=BulletType.STRATEGY, section="section1"),
            Bullet(content="Test bullet 2", bullet_type=BulletType.ERROR_PATTERN, section="section1"),
            Bullet(content="Test bullet 3", bullet_type=BulletType.API_GUIDELINE, section="section2"),
        ]

        playbook = Playbook()
        for bullet in bullets:
            playbook.add_bullet(bullet)

        # Test network visualization
        fig = create_bullet_network_visualization(playbook)
        if fig:
            print("✅ Network visualization created successfully")
        else:
            print("⚠️ Network visualization returned None")

        # Test type distribution
        fig = create_bullet_type_distribution(playbook)
        if fig:
            print("✅ Type distribution chart created successfully")
        else:
            print("⚠️ Type distribution chart returned None")

        # Test heatmap
        fig = create_bullet_heatmap(playbook)
        if fig:
            print("✅ Bullet heatmap created successfully")
        else:
            print("⚠️ Bullet heatmap returned None")

        return True

    except Exception as e:
        print(f"❌ Failed to create visualizations: {e}")
        return False

def test_session_data_export():
    """Test session data export functionality"""
    print("\n🔍 Testing session data export...")

    try:
        from ace.streamlit_utils import export_session_data

        # Create mock session state
        session_state = {
            'query_history': [
                {
                    'query': 'test query',
                    'success': True,
                    'timestamp': datetime.datetime.now().isoformat(),
                    'generated_code': 'print("hello world")'
                }
            ],
            'config_loaded': True
        }

        # Export data
        json_data = export_session_data(session_state)

        # Validate JSON
        data = json.loads(json_data)

        if 'query_history' in data and len(data['query_history']) > 0:
            print("✅ Session data export successful")
            print(f"   Exported {len(data['query_history'])} query entries")
            return True
        else:
            print("❌ Invalid session data export")
            return False

    except Exception as e:
        print(f"❌ Failed to export session data: {e}")
        return False

def test_file_operations():
    """Test file upload/download operations"""
    print("\n🔍 Testing file operations...")

    try:
        from ace import Playbook, Bullet, BulletType
        import json

        # Create test playbook
        playbook = Playbook()
        test_bullet = Bullet(
            content="Test file operation bullet",
            bullet_type=BulletType.STRATEGY,
            section="file_test"
        )
        playbook.add_bullet(test_bullet)

        # Test serialization
        playbook_dict = playbook.model_dump()
        json_str = json.dumps(playbook_dict, indent=2, default=str)

        # Test deserialization
        loaded_dict = json.loads(json_str)
        loaded_playbook = Playbook(**loaded_dict)

        if len(loaded_playbook.bullets) == len(playbook.bullets):
            print("✅ File operations (serialize/deserialize) successful")
            return True
        else:
            print("❌ File operations failed - bullet count mismatch")
            return False

    except Exception as e:
        print(f"❌ File operations failed: {e}")
        return False

def test_streamlit_app_syntax():
    """Test that the Streamlit app has valid Python syntax"""
    print("\n🔍 Testing Streamlit app syntax...")

    try:
        import ast

        # Check main app
        with open('streamlit_app.py', 'r') as f:
            app_code = f.read()

        ast.parse(app_code)
        print("✅ streamlit_app.py syntax is valid")

        # Check utilities
        with open('ace/streamlit_utils.py', 'r') as f:
            utils_code = f.read()

        ast.parse(utils_code)
        print("✅ ace/streamlit_utils.py syntax is valid")

        # Check startup script
        with open('run_streamlit.py', 'r') as f:
            startup_code = f.read()

        ast.parse(startup_code)
        print("✅ run_streamlit.py syntax is valid")

        return True

    except SyntaxError as e:
        print(f"❌ Syntax error in Streamlit files: {e}")
        return False
    except FileNotFoundError as e:
        print(f"❌ Missing required file: {e}")
        return False
    except Exception as e:
        print(f"❌ Error checking Streamlit app syntax: {e}")
        return False

def test_configuration():
    """Test configuration loading"""
    print("\n🔍 Testing configuration...")

    try:
        from ace.config_loader import get_ace_config

        config = get_ace_config()

        # Check required config fields
        required_fields = [
            'generator_model',
            'reflector_model',
            'curator_model',
            'max_reflector_rounds',
            'max_epochs',
            'max_playbook_bullets'
        ]

        for field in required_fields:
            if hasattr(config, field):
                print(f"   ✅ {field}: {getattr(config, field)}")
            else:
                print(f"   ⚠️ Missing field: {field}")

        print("✅ Configuration loaded successfully")
        return True

    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 ACE Framework Streamlit Application Test Suite")
    print("=" * 60)

    tests = [
        ("Import Tests", test_imports),
        ("Configuration Tests", test_configuration),
        ("ACE Initialization Tests", test_ace_initialization),
        ("Playbook Creation Tests", test_playbook_creation),
        ("Visualization Tests", test_visualizations),
        ("Session Export Tests", test_session_data_export),
        ("File Operations Tests", test_file_operations),
        ("Streamlit App Syntax Tests", test_streamlit_app_syntax),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")

        try:
            if test_name == "ACE Initialization Tests":
                result = test_func()
                results.append((test_name, result is not False))
            else:
                result = test_func()
                results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))

    # Summary
    print(f"\n{'='*60}")
    print("📊 Test Results Summary")
    print(f"{'='*60}")

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<30} {status}")
        if result:
            passed += 1

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! The Streamlit application is ready to use.")
        print("\n📋 Next steps:")
        print("1. Run: python run_streamlit.py")
        print("2. Open: http://localhost:8501")
        print("3. Initialize ACE Framework in the sidebar")
        print("4. Start exploring the dashboard!")
    else:
        print("⚠️ Some tests failed. Please fix the issues before running the application.")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())