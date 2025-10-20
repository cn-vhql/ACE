#!/usr/bin/env python3
"""
Startup script for ACE Framework Streamlit Dashboard
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        'streamlit',
        'plotly',
        'networkx',
        'pandas',
        'pydantic',
        'yaml'
    ]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n💡 Install them with:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False

    print("✅ All dependencies are installed!")
    return True

def check_config():
    """Check if configuration files exist"""
    config_files = ['config.yaml']
    missing_files = []

    for file in config_files:
        if not Path(file).exists():
            missing_files.append(file)

    if missing_files:
        print("⚠️  Missing configuration files:")
        for file in missing_files:
            print(f"   - {file}")
        print("\n💡 The app will use default configuration.")

    return True

def start_streamlit(port=8501, host='localhost', debug=False):
    """Start the Streamlit application"""

    # Streamlit command
    cmd = [
        'streamlit', 'run', 'streamlit_app.py',
        '--server.port', str(port),
        '--server.address', host,
        '--server.headless', 'false'
    ]

    if debug:
        cmd.extend(['--logger.level', 'debug'])

    print(f"🚀 Starting ACE Framework Dashboard...")
    print(f"📡 URL: http://{host}:{port}")
    print(f"🔧 Debug mode: {'on' if debug else 'off'}")
    print("=" * 50)

    try:
        # Start Streamlit
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start Streamlit: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Shutting down ACE Framework Dashboard...")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Start ACE Framework Streamlit Dashboard"
    )

    parser.add_argument(
        '--port', '-p',
        type=int,
        default=8501,
        help='Port to run the dashboard on (default: 8501)'
    )

    parser.add_argument(
        '--host', '-H',
        type=str,
        default='localhost',
        help='Host to bind the dashboard to (default: localhost)'
    )

    parser.add_argument(
        '--debug', '-d',
        action='store_true',
        help='Enable debug mode'
    )

    parser.add_argument(
        '--skip-deps-check',
        action='store_true',
        help='Skip dependency checking'
    )

    args = parser.parse_args()

    print("🧠 ACE Framework Streamlit Dashboard")
    print("=" * 50)

    # Check dependencies
    if not args.skip_deps_check:
        print("🔍 Checking dependencies...")
        if not check_dependencies():
            sys.exit(1)

    # Check configuration
    print("🔍 Checking configuration...")
    check_config()

    # Start Streamlit
    start_streamlit(
        port=args.port,
        host=args.host,
        debug=args.debug
    )

if __name__ == "__main__":
    main()