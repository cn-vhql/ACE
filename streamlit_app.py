"""
ACE Framework Streamlit Web Interface
A comprehensive interactive dashboard for the ACE framework
"""
import streamlit as st
import asyncio
import json
import time
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional
import plotly.express as px
import plotly.graph_objects as go
from io import StringIO, BytesIO
import base64

# ACE Framework imports
from ace import ACE, ACEConfig, Playbook, Bullet, BulletType, BulletTag
from ace.config_loader import get_ace_config, load_config
from ace.mcp_client import MCPToolManager

# Global variable to track utility availability
UTILS_AVAILABLE = None

def ensure_utils_available():
    """Check and import streamlit utilities when needed"""
    global UTILS_AVAILABLE
    if UTILS_AVAILABLE is None:
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
            UTILS_AVAILABLE = {
                'create_bullet_network_visualization': create_bullet_network_visualization,
                'create_trajectory_timeline': create_trajectory_timeline,
                'create_playbook_evolution_chart': create_playbook_evolution_chart,
                'create_bullet_type_distribution': create_bullet_type_distribution,
                'create_performance_metrics': create_performance_metrics,
                'create_query_analysis_dashboard': create_query_analysis_dashboard,
                'display_trajectory_details': display_trajectory_details,
                'display_reflection_details': display_reflection_details,
                'export_session_data': export_session_data,
                'create_bullet_heatmap': create_bullet_heatmap
            }
        except ImportError as e:
            UTILS_AVAILABLE = False
            st.error(f"❌ Failed to import visualization utilities: {e}")
            st.warning("⚠️ Some visualization features may not be available. Install missing dependencies with:")
            st.code("pip install plotly networkx pandas")

    return UTILS_AVAILABLE

# Page configuration
st.set_page_config(
    page_title="ACE Framework Dashboard",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
    }

    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
    }

    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.25rem;
        padding: 1rem;
        margin: 1rem 0;
    }

    .error-box {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 0.25rem;
        padding: 1rem;
        margin: 1rem 0;
    }

    .bullet-card {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 0.25rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }

    .trajectory-card {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 0.25rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state variables
def init_session_state():
    """Initialize session state variables"""
    if 'ace_instance' not in st.session_state:
        st.session_state.ace_instance = None
    if 'current_playbook' not in st.session_state:
        st.session_state.current_playbook = None
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []
    if 'current_trajectory' not in st.session_state:
        st.session_state.current_trajectory = None
    if 'current_reflection' not in st.session_state:
        st.session_state.current_reflection = None
    if 'config_loaded' not in st.session_state:
        st.session_state.config_loaded = False
    if 'mcp_enabled' not in st.session_state:
        st.session_state.mcp_enabled = False
    if 'mcp_manager' not in st.session_state:
        st.session_state.mcp_manager = None
    if 'mcp_tools' not in st.session_state:
        st.session_state.mcp_tools = []

# Async function runner for Streamlit
def run_async(func):
    """Run async function in Streamlit"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(func)
    finally:
        loop.close()

# Initialize ACE Framework
def initialize_ace():
    """Initialize ACE framework with configuration"""
    try:
        config = get_ace_config()
        ace = ACE(config)
        st.session_state.ace_instance = ace
        st.session_state.current_playbook = ace.playbook
        st.session_state.config_loaded = True

        # Initialize MCP if enabled in config
        mcp_config = getattr(config, 'mcp_config', {})
        if mcp_config.get('enabled', False):
            success, message = initialize_mcp()
            if success:
                st.session_state.mcp_enabled = True
                return True, f"ACE Framework initialized successfully with MCP tools!"
            else:
                st.warning(f"ACE Framework initialized but MCP failed: {message}")
                return True, "ACE Framework initialized successfully (MCP disabled)"
        else:
            st.session_state.mcp_enabled = False
            return True, "ACE Framework initialized successfully!"

    except Exception as e:
        return False, f"Failed to initialize ACE Framework: {str(e)}"

# Initialize MCP Tools
def initialize_mcp():
    """Initialize MCP tool manager"""
    try:
        if not st.session_state.ace_instance:
            return False, "ACE Framework must be initialized first"

        config = get_ace_config()
        mcp_manager = MCPToolManager(config)

        # Try to initialize MCP connections
        if run_async(mcp_manager.initialize()):
            st.session_state.mcp_manager = mcp_manager
            st.session_state.mcp_tools = mcp_manager.get_available_tools()
            return True, f"MCP initialized with {len(st.session_state.mcp_tools)} tools"
        else:
            return False, "Failed to initialize MCP connections"

    except Exception as e:
        return False, f"Failed to initialize MCP: {str(e)}"

# Toggle MCP Tools
def toggle_mcp_tools():
    """Toggle MCP tools on/off"""
    if st.session_state.mcp_enabled:
        # Disable MCP
        if st.session_state.mcp_manager:
            run_async(st.session_state.mcp_manager.cleanup())
        st.session_state.mcp_enabled = False
        st.session_state.mcp_manager = None
        st.session_state.mcp_tools = []
        return False, "MCP tools disabled"
    else:
        # Enable MCP
        success, message = initialize_mcp()
        if success:
            st.session_state.mcp_enabled = True
            return True, message
        else:
            st.session_state.mcp_enabled = False
            return False, message

# Playbook management functions
def save_playbook_to_session(playbook_data):
    """Save playbook data to session state"""
    st.session_state.current_playbook = playbook_data

def load_playbook_from_file(uploaded_file):
    """Load playbook from uploaded file"""
    try:
        content = uploaded_file.read().decode('utf-8')
        playbook_dict = json.loads(content)
        playbook = Playbook(**playbook_dict)

        if st.session_state.ace_instance:
            st.session_state.ace_instance.playbook = playbook

        st.session_state.current_playbook = playbook
        return True, "Playbook loaded successfully!"
    except Exception as e:
        return False, f"Failed to load playbook: {str(e)}"

def download_playbook():
    """Download current playbook as JSON"""
    if st.session_state.current_playbook:
        playbook_dict = st.session_state.current_playbook.model_dump()
        json_str = json.dumps(playbook_dict, indent=2, default=str)

        # Create download button
        b64 = base64.b64encode(json_str.encode()).decode()
        href = f'<a href="data:file/json;base64,{b64}" download="playbook_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json">Download Playbook JSON</a>'
        st.markdown(href, unsafe_allow_html=True)

# Main dashboard components
def render_header():
    """Render main header"""
    st.markdown('<h1 class="main-header">🧠 ACE Framework Dashboard</h1>', unsafe_allow_html=True)
    st.markdown("---")

def render_sidebar():
    """Render sidebar with navigation and controls"""
    with st.sidebar:
        st.header("🎛️ Control Panel")

        # Initialize ACE Framework
        if not st.session_state.config_loaded:
            if st.button("🚀 Initialize ACE Framework", type="primary"):
                with st.spinner("Initializing ACE Framework..."):
                    success, message = initialize_ace()
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

        if st.session_state.config_loaded:
            st.success("✅ ACE Framework Ready")

            # MCP Status and Controls
            st.header("🔧 MCP Tools")
            mcp_status = "🟢 Enabled" if st.session_state.mcp_enabled else "🔴 Disabled"
            st.write(f"Status: {mcp_status}")

            if st.session_state.mcp_enabled:
                st.info(f"📋 {len(st.session_state.mcp_tools)} MCP tools available")
                if st.button("🔄 Disable MCP Tools"):
                    success, message = toggle_mcp_tools()
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
                    st.rerun()
            else:
                if st.button("🚀 Enable MCP Tools"):
                    success, message = toggle_mcp_tools()
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

            # Navigation
            st.header("📍 Navigation")
            page = st.selectbox(
                "Select Page",
                ["🏠 Dashboard", "💬 Q&A Interface", "🔧 MCP Tools Manager", "📚 Playbook Manager",
                 "📊 Statistics", "⚙️ Configuration", "🧪 Batch Processing"]
            )

            # Quick Actions
            st.header("⚡ Quick Actions")
            if st.button("🔄 Reset Playbook"):
                if st.session_state.ace_instance:
                    st.session_state.ace_instance.reset_playbook()
                    st.session_state.current_playbook = st.session_state.ace_instance.playbook
                    st.success("Playbook reset successfully!")
                    st.rerun()

            if st.button("💾 Save Current Session"):
                save_session_data()

            return page

    return "🏠 Dashboard"

def render_dashboard_overview():
    """Render main dashboard overview"""
    col1, col2, col3, col4 = st.columns(4)

    if st.session_state.ace_instance:
        stats = st.session_state.ace_instance.get_statistics()
        playbook_summary = st.session_state.ace_instance.get_playbook_summary()

        with col1:
            st.metric(
                label="📚 Total Bullets",
                value=playbook_summary['total_bullets'],
                delta=None
            )

        with col2:
            st.metric(
                label="🎯 Success Rate",
                value=f"{stats['success_rate']:.2%}",
                delta=None
            )

        with col3:
            st.metric(
                label="🔄 Total Trajectories",
                value=stats['total_trajectories'],
                delta=None
            )

        with col4:
            st.metric(
                label="💡 Total Reflections",
                value=stats['total_reflections'],
                delta=None
            )

    # Recent Activity
    st.subheader("📈 Recent Activity")

    if st.session_state.query_history:
        recent_queries = st.session_state.query_history[-5:]
        for query_data in recent_queries:
            with st.expander(f"🔍 {query_data['query'][:50]}..."):
                st.write(f"**Status:** {'✅ Success' if query_data['success'] else '❌ Failed'}")
                st.write(f"**Time:** {query_data['timestamp']}")
                if query_data.get('generated_code'):
                    st.code(query_data['generated_code'], language='python')
    else:
        st.info("No queries yet. Start with the Q&A interface!")

def render_qa_interface():
    """Render Q&A interface"""
    st.header("💬 Interactive Q&A Interface")

    if not st.session_state.config_loaded:
        st.warning("Please initialize ACE Framework first!")
        return

    # Query input
    col1, col2 = st.columns([4, 1])

    with col1:
        query = st.text_area(
            "🔍 Enter your query:",
            placeholder="e.g., Write a Python function to calculate factorial of a number...",
            height=100
        )

    with col2:
        st.write("")  # Spacer
        st.write("")  # Spacer
        if st.button("🚀 Solve", type="primary", disabled=not query):
            # Get MCP enabled state from the checkbox
            enable_mcp = st.session_state.get('enable_mcp_checkbox', st.session_state.mcp_enabled)
            solve_query(query, enable_mcp)

    # Context options
    with st.expander("🎛️ Advanced Options"):
        col1, col2 = st.columns(2)
        with col1:
            update_playbook = st.checkbox("📚 Update Playbook", value=True)
            enable_mcp = st.checkbox("🔧 Enable MCP Tools", value=st.session_state.mcp_enabled, disabled=not st.session_state.mcp_enabled, key='enable_mcp_checkbox')
            temperature = st.slider("🌡️ Temperature", 0.0, 1.0, 0.7, 0.1)

        with col2:
            max_tokens = st.slider("📏 Max Tokens", 512, 4096, 2048, 256)
            context_info = st.text_area("Additional Context", height=100)

        # MCP tools info
        if st.session_state.mcp_enabled and enable_mcp:
            st.info(f"🔧 {len(st.session_state.mcp_tools)} MCP tools will be available for this query")
        elif not st.session_state.mcp_enabled:
            st.warning("⚠️ MCP tools are disabled. Enable them from the sidebar to use external tools.")

    # Results display
    if st.session_state.current_trajectory:
        st.subheader("📊 Results")

        trajectory = st.session_state.current_trajectory

        # Success/Failure indicator
        if trajectory.success:
            st.success("✅ Query solved successfully!")
        else:
            st.error("❌ Query failed")

        # MCP Tool Calls Display
        if trajectory.metadata.get("tools_enabled") and trajectory.metadata.get("tool_calls"):
            st.subheader("🔧 MCP Tool Calls")

            tool_calls = trajectory.metadata.get("tool_calls", [])
            for i, tool_call in enumerate(tool_calls, 1):
                with st.expander(f"🔧 Tool Call {i}: {tool_call['tool_name']}"):
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        st.write(f"**Tool:** {tool_call['tool_name']}")
                        st.write(f"**Success:** {'✅ Yes' if tool_call['success'] else '❌ No'}")
                        if tool_call.get('arguments'):
                            st.write("**Arguments:**")
                            st.json(tool_call['arguments'])

                    with col2:
                        if tool_call['success']:
                            st.success("Executed Successfully")
                            if tool_call.get('result'):
                                with st.expander("View Result", expanded=False):
                                    if isinstance(tool_call['result'], str) and len(tool_call['result']) > 500:
                                        st.text(tool_call['result'][:500] + "...")
                                    else:
                                        st.json(tool_call['result'] if isinstance(tool_call['result'], dict) else {"result": str(tool_call['result'])})
                        else:
                            st.error("Execution Failed")
                            if tool_call.get('error'):
                                st.error(f"Error: {tool_call['error']}")

            st.info(f"📊 Total: {len(tool_calls)} tool calls executed")

        elif trajectory.metadata.get("tools_enabled"):
            st.info("🔧 MCP tools were enabled but no tool calls were made for this query")

        # Use enhanced trajectory details display
        utils = ensure_utils_available()
        if utils and utils is not False:
            utils['display_trajectory_details'](trajectory)

            # Enhanced reflection display
            if st.session_state.current_reflection:
                st.subheader("🔍 Reflection Analysis")
                utils['display_reflection_details'](st.session_state.current_reflection)

            # Visualization options
            st.subheader("📈 Visualizations")

            viz_col1, viz_col2 = st.columns(2)

            with viz_col1:
                if st.button("🕸️ Show Bullet Network"):
                    if st.session_state.current_playbook:
                        try:
                            fig = utils['create_bullet_network_visualization'](st.session_state.current_playbook)
                            if fig:
                                st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.info("No bullets to visualize")
                        except Exception as e:
                            st.error(f"Error creating network visualization: {str(e)}")
                            st.info("This may be due to missing dependencies or insufficient data")

            with viz_col2:
                if st.button("📊 Create Timeline"):
                    if st.session_state.query_history:
                        try:
                            trajectories = [data.get('trajectory') for data in st.session_state.query_history if data.get('trajectory')]
                            fig = utils['create_trajectory_timeline'](trajectories)
                            if fig:
                                st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.info("No trajectory data available")
                        except Exception as e:
                            st.error(f"Error creating timeline: {str(e)}")
                            st.info("This may be due to missing dependencies or insufficient data")
        else:
            # Fallback display without enhanced utilities
            st.info("⚠️ Enhanced visualization features are not available. Install missing dependencies:")
            st.code("pip install plotly networkx pandas")

def solve_query(query: str, enable_mcp: bool = None):
    """Solve a query using ACE framework"""
    if enable_mcp is None:
        enable_mcp = st.session_state.mcp_enabled

    with st.spinner("🤖 Thinking..."):
        try:
            # Use ACE's solve_query method with MCP support
            trajectory, reflection = run_async(
                st.session_state.ace_instance.solve_query(
                    query=query,
                    update_playbook=True,
                    enable_tools=enable_mcp
                )
            )

            st.session_state.current_trajectory = trajectory
            st.session_state.current_reflection = reflection

            # Add to history with MCP info
            query_data = {
                'query': query,
                'success': trajectory.success,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'generated_code': trajectory.generated_code,
                'mcp_enabled': enable_mcp,
                'tool_calls': len(trajectory.metadata.get('tool_calls', [])),
                'trajectory': trajectory
            }
            st.session_state.query_history.append(query_data)

            st.rerun()

        except Exception as e:
            st.error(f"❌ Error solving query: {str(e)}")

def render_mcp_tools_manager():
    """Render MCP tools management interface"""
    st.header("🔧 MCP Tools Manager")

    if not st.session_state.config_loaded:
        st.warning("Please initialize ACE Framework first!")
        return

    # MCP Status Overview
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        status_color = "🟢" if st.session_state.mcp_enabled else "🔴"
        st.metric("MCP Status", f"{status_color} {'Enabled' if st.session_state.mcp_enabled else 'Disabled'}")

    with col2:
        st.metric("Available Tools", len(st.session_state.mcp_tools))

    with col3:
        # Count successful tool calls from history
        successful_calls = sum(1 for q in st.session_state.query_history if q.get('mcp_enabled', False) and q.get('tool_calls', 0) > 0)
        st.metric("Queries with Tools", successful_calls)

    with col4:
        total_tool_calls = sum(q.get('tool_calls', 0) for q in st.session_state.query_history)
        st.metric("Total Tool Calls", total_tool_calls)

    # MCP Controls
    st.subheader("🎛️ MCP Controls")

    col1, col2 = st.columns(2)

    with col1:
        if st.session_state.mcp_enabled:
            if st.button("🔄 Disable MCP Tools", type="secondary"):
                success, message = toggle_mcp_tools()
                if success:
                    st.success(message)
                else:
                    st.error(message)
                st.rerun()
        else:
            if st.button("🚀 Enable MCP Tools", type="primary"):
                success, message = toggle_mcp_tools()
                if success:
                    st.success(message)
                else:
                    st.error(message)
                st.rerun()

    with col2:
        if st.button("🔄 Refresh MCP Tools", disabled=not st.session_state.mcp_enabled):
            success, message = initialize_mcp()
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)

    # Tools List
    if st.session_state.mcp_enabled and st.session_state.mcp_tools:
        st.subheader("📋 Available MCP Tools")

        # Group tools by server
        tools_by_server = {}
        for tool in st.session_state.mcp_tools:
            if tool.server_name not in tools_by_server:
                tools_by_server[tool.server_name] = []
            tools_by_server[tool.server_name].append(tool)

        # Display tools by server
        for server_name, server_tools in tools_by_server.items():
            with st.expander(f"🖥️ {server_name.title()} Server ({len(server_tools)} tools)"):
                for tool in server_tools:
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        st.write(f"**{tool.name}**")
                        st.caption(tool.description)

                        # Show input schema if available
                        if tool.input_schema and "properties" in tool.input_schema:
                            with st.expander(f"Parameters for {tool.name}", expanded=False):
                                for param_name, param_info in tool.input_schema["properties"].items():
                                    param_type = param_info.get("type", "unknown")
                                    param_desc = param_info.get("description", "")
                                    required = param_name in tool.input_schema.get("required", [])
                                    req_marker = " ⚠️ Required" if required else ""
                                    st.write(f"- **{param_name}** ({param_type}{req_marker}): {param_desc}")

                    with col2:
                        if st.button(f"🧪 Test", key=f"test_{tool.server_name}_{tool.name}"):
                            st.session_state[f"test_tool_{tool.server_name}_{tool.name}"] = True

                    # Tool testing interface
                    if st.session_state.get(f"test_tool_{tool.server_name}_{tool.name}", False):
                        st.write("---")
                        st.write(f"🧪 **Test {tool.name}**")

                        # Build form based on input schema
                        test_args = {}
                        if tool.input_schema and "properties" in tool.input_schema:
                            for param_name, param_info in tool.input_schema["properties"].items():
                                param_type = param_info.get("type", "string")
                                required = param_name in tool.input_schema.get("required", [])

                                if param_type == "string":
                                    default_value = ""
                                    if "example" in param_info:
                                        default_value = param_info["example"]
                                    elif param_name == "path":
                                        default_value = "test.txt"
                                    elif param_name == "query":
                                        default_value = "test query"

                                    test_args[param_name] = st.text_input(
                                        f"{param_name} ({'required' if required else 'optional'})",
                                        value=default_value,
                                        key=f"arg_{tool.server_name}_{tool.name}_{param_name}"
                                    )
                                elif param_type == "integer":
                                    test_args[param_name] = st.number_input(
                                        f"{param_name} ({'required' if required else 'optional'})",
                                        value=param_info.get("default", 1),
                                        key=f"arg_{tool.server_name}_{tool.name}_{param_name}"
                                    )
                                elif param_type == "boolean":
                                    test_args[param_name] = st.checkbox(
                                        f"{param_name}",
                                        value=param_info.get("default", False),
                                        key=f"arg_{tool.server_name}_{tool.name}_{param_name}"
                                    )

                        # Execute tool test
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(f"🚀 Execute {tool.name}", key=f"execute_{tool.server_name}_{tool.name}"):
                                with st.spinner(f"Executing {tool.name}..."):
                                    try:
                                        result = run_async(
                                            st.session_state.mcp_manager.call_tool(
                                                f"{tool.server_name}.{tool.name}",
                                                test_args
                                            )
                                        )

                                        if result.success:
                                            st.success("✅ Tool executed successfully!")
                                            st.json({
                                                "result": result.result,
                                                "arguments": result.arguments
                                            })
                                        else:
                                            st.error(f"❌ Tool execution failed: {result.error}")

                                    except Exception as e:
                                        st.error(f"❌ Error executing tool: {str(e)}")

                        with col2:
                            if st.button(f"❌ Close Test", key=f"close_{tool.server_name}_{tool.name}"):
                                st.session_state[f"test_tool_{tool.server_name}_{tool.name}"] = False
                                st.rerun()

    elif st.session_state.mcp_enabled:
        st.info("🔍 No MCP tools available. Check your configuration.")
    else:
        st.warning("⚠️ MCP tools are disabled. Enable them to see available tools.")

    # Tool Usage Statistics
    if st.session_state.query_history:
        st.subheader("📊 Tool Usage Statistics")

        # Filter queries with MCP enabled
        mcp_queries = [q for q in st.session_state.query_history if q.get('mcp_enabled', False)]

        if mcp_queries:
            # Create DataFrame for analysis
            mcp_df = pd.DataFrame(mcp_queries)

            col1, col2 = st.columns(2)

            with col1:
                # Success rate with MCP tools
                mcp_success_rate = mcp_df['success'].mean()
                st.metric("Success Rate with MCP", f"{mcp_success_rate:.2%}")

                # Tool calls per query
                avg_tool_calls = mcp_df['tool_calls'].mean()
                st.metric("Avg Tool Calls per Query", f"{avg_tool_calls:.1f}")

            with col2:
                # Tool usage over time
                if len(mcp_df) > 1:
                    mcp_df['timestamp'] = pd.to_datetime(mcp_df['timestamp'])
                    mcp_df = mcp_df.sort_values('timestamp')
                    mcp_df['cumulative_tool_calls'] = mcp_df['tool_calls'].cumsum()

                    fig = px.line(
                        mcp_df,
                        x='timestamp',
                        y='cumulative_tool_calls',
                        title="Cumulative Tool Usage Over Time",
                        labels={'cumulative_tool_calls': 'Total Tool Calls', 'timestamp': 'Time'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Need more queries to show usage trends")

        else:
            st.info("No queries have been processed with MCP tools yet.")

    # Configuration Info
    st.subheader("⚙️ MCP Configuration")

    try:
        config = get_ace_config()
        mcp_config = getattr(config, 'mcp_config', {})

        col1, col2 = st.columns(2)

        with col1:
            st.write("**MCP Configuration:**")
            st.json({
                "enabled": mcp_config.get('enabled', False),
                "servers": list(mcp_config.get('servers', {}).keys()),
                "max_concurrent_calls": mcp_config.get('settings', {}).get('max_concurrent_calls', 'N/A'),
                "default_timeout": mcp_config.get('settings', {}).get('default_timeout', 'N/A')
            })

        with col2:
            st.write("**Recent Tool Calls (Last 5):**")
            recent_tool_calls = []
            for query_data in reversed(st.session_state.query_history[-5:]):
                if query_data.get('tool_calls', 0) > 0:
                    recent_tool_calls.append({
                        'query': query_data['query'][:50] + "...",
                        'tool_calls': query_data['tool_calls'],
                        'success': query_data['success'],
                        'time': query_data['timestamp']
                    })

            if recent_tool_calls:
                for call in recent_tool_calls:
                    status = "✅" if call['success'] else "❌"
                    st.write(f"{status} **{call['tool_calls']} tools** - {call['query']}")
                    st.caption(f"📅 {call['time']}")
            else:
                st.write("No recent tool calls")

    except Exception as e:
        st.error(f"Error loading MCP configuration: {str(e)}")

def render_playbook_manager():
    """Render playbook management interface"""
    st.header("📚 Playbook Manager")

    if not st.session_state.config_loaded:
        st.warning("Please initialize ACE Framework first!")
        return

    # Playbook actions
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📁 Upload Playbook"):
            st.session_state.show_upload = True

    with col2:
        if st.button("💾 Download Playbook"):
            download_playbook()

    with col3:
        if st.button("🔄 Reload from ACE"):
            st.session_state.current_playbook = st.session_state.ace_instance.playbook
            st.success("Playbook reloaded!")

    with col4:
        if st.button("🗑️ Clear Playbook"):
            st.session_state.ace_instance.reset_playbook()
            st.session_state.current_playbook = st.session_state.ace_instance.playbook
            st.success("Playbook cleared!")

    # File upload
    if st.session_state.get('show_upload', False):
        st.subheader("📁 Upload Playbook")
        uploaded_file = st.file_uploader(
            "Choose a JSON file",
            type=['json'],
            key="playbook_upload"
        )

        if uploaded_file:
            success, message = load_playbook_from_file(uploaded_file)
            if success:
                st.success(message)
                st.session_state.show_upload = False
                st.rerun()
            else:
                st.error(message)

    # Playbook summary
    if st.session_state.current_playbook:
        st.subheader("📊 Playbook Summary")

        summary = st.session_state.ace_instance.get_playbook_summary()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Bullets", summary['total_bullets'])

        with col2:
            st.metric("Sections", len(summary['sections']))

        with col3:
            helpful_bullets = summary['helpfulness_stats']['helpful']
            total_bullets = summary['total_bullets']
            helpful_ratio = helpful_bullets / total_bullets if total_bullets > 0 else 0
            st.metric("Helpful Ratio", f"{helpful_ratio:.2%}")

        # Sections breakdown
        if summary['sections']:
            st.subheader("📑 Sections")
            sections_df = pd.DataFrame([
                {"Section": section, "Bullets": count}
                for section, count in summary['sections'].items()
            ])

            fig = px.pie(
                sections_df,
                values="Bullets",
                names="Section",
                title="Bullets by Section"
            )
            st.plotly_chart(fig, use_container_width=True)

        # Bullet types breakdown
        if summary['bullet_types']:
            st.subheader("🏷️ Bullet Types")
            types_df = pd.DataFrame([
                {"Type": bullet_type, "Count": count}
                for bullet_type, count in summary['bullet_types'].items()
            ])

            fig = px.bar(
                types_df,
                x="Type",
                y="Count",
                title="Bullets by Type"
            )
            st.plotly_chart(fig, use_container_width=True)

        # Enhanced visualizations
        st.subheader("📊 Playbook Visualizations")

        utils = ensure_utils_available()
        if utils and utils is not False:
            viz_col1, viz_col2 = st.columns(2)

            with viz_col1:
                if st.button("🔥 Show Bullet Heatmap"):
                    try:
                        fig = utils['create_bullet_heatmap'](st.session_state.current_playbook)
                        if fig:
                            st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.error(f"Error creating heatmap: {str(e)}")
                        st.info("This may be due to missing dependencies or insufficient data")

            with viz_col2:
                if st.button("🎯 Show Bullet Network"):
                    try:
                        fig = utils['create_bullet_network_visualization'](st.session_state.current_playbook)
                        if fig:
                            st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.error(f"Error creating network visualization: {str(e)}")
                        st.info("This may be due to missing dependencies or insufficient data")
        else:
            st.info("⚠️ Visualization features require plotly and networkx packages")
            st.code("pip install plotly networkx pandas")

        # Browse bullets
        st.subheader("📖 Browse Bullets")

        # Filter options
        col1, col2, col3 = st.columns(3)

        with col1:
            selected_section = st.selectbox(
                "Filter by Section",
                ["All"] + list(summary['sections'].keys())
            )

        with col2:
            selected_type = st.selectbox(
                "Filter by Type",
                ["All"] + list(summary['bullet_types'].keys())
            )

        with col3:
            selected_tag = st.selectbox(
                "Filter by Tag",
                ["All", "helpful", "harmful", "neutral"]
            )

        # Display filtered bullets
        bullets_to_display = st.session_state.current_playbook.bullets

        if selected_section != "All":
            bullets_to_display = [
                b for b in bullets_to_display
                if b.section == selected_section
            ]

        if selected_type != "All":
            bullets_to_display = [
                b for b in bullets_to_display
                if b.bullet_type.value == selected_type
            ]

        if selected_tag != "All":
            bullets_to_display = [
                b for b in bullets_to_display
                if b.tag().value == selected_tag
            ]

        # Display bullets with pagination
        items_per_page = 10
        total_pages = max(1, (len(bullets_to_display) + items_per_page - 1) // items_per_page)

        if total_pages > 1:
            page = st.number_input(
                "Page",
                min_value=1,
                max_value=total_pages,
                value=1,
                step=1
            )

            start_idx = (page - 1) * items_per_page
            end_idx = start_idx + items_per_page
            bullets_to_display = bullets_to_display[start_idx:end_idx]

        for bullet in bullets_to_display:
            with st.expander(f"📌 {bullet.bullet_type.value.title()}: {bullet.content[:50]}..."):
                st.write(f"**Content:** {bullet.content}")
                st.write(f"**Section:** {bullet.section}")
                st.write(f"**Type:** {bullet.bullet_type.value}")
                st.write(f"**Tag:** {bullet.tag().value}")
                st.write(f"**Helpful:** {bullet.helpful_count} | **Harmful:** {bullet.harmful_count}")
                st.write(f"**Created:** {bullet.created_at.strftime('%Y-%m-%d %H:%M:%S')}")

def render_statistics():
    """Render statistics and monitoring dashboard"""
    st.header("📊 Statistics & Monitoring")

    if not st.session_state.config_loaded:
        st.warning("Please initialize ACE Framework first!")
        return

    stats = st.session_state.ace_instance.get_statistics()
    playbook_summary = st.session_state.ace_instance.get_playbook_summary()

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Success Rate", f"{stats['success_rate']:.2%}")

    with col2:
        st.metric("Total Queries", stats['total_trajectories'])

    with col3:
        st.metric("Playbook Size", stats['playbook_size'])

    with col4:
        st.metric("Delta Updates", stats['total_delta_updates'])

    # Success rate over time (simulated data)
    st.subheader("📈 Performance Trends")

    if st.session_state.query_history:
        # Create success rate over time data
        df = pd.DataFrame(st.session_state.query_history)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')

        # Calculate rolling success rate
        df['rolling_success'] = df['success'].rolling(window=min(10, len(df)), min_periods=1).mean()

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['rolling_success'],
            mode='lines+markers',
            name='Rolling Success Rate',
            line=dict(color='green', width=2)
        ))

        fig.update_layout(
            title="Success Rate Over Time",
            xaxis_title="Time",
            yaxis_title="Success Rate",
            yaxis=dict(tickformat='.1%')
        )

        st.plotly_chart(fig, use_container_width=True)

    # Query distribution
    if st.session_state.query_history:
        st.subheader("📊 Query Analysis")

        try:
            df = pd.DataFrame(st.session_state.query_history)

            # Ensure we have the required columns
            if 'success' not in df.columns or df.empty:
                st.warning("⚠️ Insufficient query data for analysis")
                return

            col1, col2 = st.columns(2)

            with col1:
                # Success/Failure pie chart
                success_counts = df['success'].value_counts()
                if len(success_counts) > 0:
                    # Create proper labels for the pie chart
                    labels = []
                    for success_val in success_counts.index:
                        labels.append('Success' if success_val else 'Failure')

                    fig = px.pie(
                        values=success_counts.values,
                        names=labels,
                        title="Query Success Rate"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No query data to display")

            with col2:
                # Queries per hour
                if 'timestamp' in df.columns:
                    try:
                        df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
                        hourly_counts = df['hour'].value_counts().sort_index()

                        if len(hourly_counts) > 0:
                            fig = px.bar(
                                x=hourly_counts.index,
                                y=hourly_counts.values,
                                title="Queries by Hour of Day"
                            )
                            fig.update_xaxes(title="Hour")
                            fig.update_yaxes(title="Number of Queries")
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("No hourly data to display")
                    except Exception as e:
                        st.warning(f"Error creating hourly chart: {str(e)}")
                else:
                    st.info("No timestamp data available for hourly analysis")

        except Exception as e:
            st.error(f"Error analyzing query data: {str(e)}")
            st.info("This may be due to missing data or format issues")

def render_configuration():
    """Render configuration management interface"""
    st.header("⚙️ Configuration Management")

    try:
        config = get_ace_config()

        st.subheader("📋 Current Configuration")

        # Model configuration
        st.write("**Model Configuration**")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.text_input("Generator Model", value=config.generator_model, disabled=True)

        with col2:
            st.text_input("Reflector Model", value=config.reflector_model, disabled=True)

        with col3:
            st.text_input("Curator Model", value=config.curator_model, disabled=True)

        # ACE parameters
        st.write("**ACE Framework Parameters**")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.number_input(
                "Max Reflector Rounds",
                value=config.max_reflector_rounds,
                disabled=True
            )

        with col2:
            st.number_input(
                "Max Epochs",
                value=config.max_epochs,
                disabled=True
            )

        with col3:
            st.number_input(
                "Max Playbook Bullets",
                value=config.max_playbook_bullets,
                disabled=True
            )

        # Provider information
        st.write("**LLM Provider Information**")
        provider_type = getattr(config, 'provider_type', 'Unknown')
        st.info(f"Current Provider: {provider_type}")

        if hasattr(config, 'openai_base_url'):
            st.text_input("API Base URL", value=config.openai_base_url, disabled=True)

    except Exception as e:
        st.error(f"Failed to load configuration: {str(e)}")

def render_batch_processing():
    """Render batch processing interface"""
    st.header("🧪 Batch Processing & Evaluation")

    if not st.session_state.config_loaded:
        st.warning("Please initialize ACE Framework first!")
        return

    # Batch query processing
    st.subheader("📦 Batch Query Processing")

    # Query input
    queries = st.text_area(
        "Enter queries (one per line):",
        placeholder="Query 1\nQuery 2\nQuery 3...",
        height=150
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        update_playbook = st.checkbox("Update Playbook", value=True)

    with col2:
        epochs = st.number_input("Epochs", min_value=1, max_value=10, value=1)

    with col3:
        if st.button("🚀 Process Batch", type="primary", disabled=not queries):
            process_batch_queries(queries, update_playbook, epochs)

    # Performance evaluation
    st.subheader("📊 Performance Evaluation")

    test_queries = st.text_area(
        "Test queries (one per line):",
        placeholder="Test Query 1\nTest Query 2\nTest Query 3...",
        height=100
    )

    if st.button("🧪 Run Evaluation", disabled=not test_queries):
        run_evaluation(test_queries)

def process_batch_queries(queries_str: str, update_playbook: bool, epochs: int):
    """Process batch queries"""
    queries = [q.strip() for q in queries_str.split('\n') if q.strip()]

    if not queries:
        st.warning("Please enter at least one query!")
        return

    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        for epoch in range(epochs):
            status_text.text(f"Processing epoch {epoch + 1}/{epochs}...")

            for i, query in enumerate(queries):
                progress = (epoch * len(queries) + i + 1) / (epochs * len(queries))
                progress_bar.progress(progress)

                trajectory, reflection = run_async(
                    st.session_state.ace_instance.solve_query(
                        query,
                        update_playbook=update_playbook,
                        enable_tools=st.session_state.mcp_enabled
                    )
                )

                # Add to history
                query_data = {
                    'query': query,
                    'success': trajectory.success,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'generated_code': trajectory.generated_code
                }
                st.session_state.query_history.append(query_data)

        status_text.text("✅ Batch processing completed!")
        st.success(f"Processed {len(queries)} queries over {epochs} epochs")
        st.rerun()

    except Exception as e:
        status_text.text("❌ Batch processing failed!")
        st.error(f"Error: {str(e)}")

def run_evaluation(queries_str: str):
    """Run performance evaluation"""
    queries = [q.strip() for q in queries_str.split('\n') if q.strip()]

    if not queries:
        st.warning("Please enter at least one test query!")
        return

    with st.spinner("Running evaluation..."):
        try:
            results = run_async(
                st.session_state.ace_instance.evaluate_performance(
                    queries,
                    enable_tools=st.session_state.mcp_enabled
                )
            )

            st.subheader("📊 Evaluation Results")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Success Rate", f"{results['success_rate']:.2%}")

            with col2:
                st.metric("Total Queries", results['total_queries'])

            with col3:
                st.metric("Avg Confidence", f"{results['average_confidence']:.2%}")

            # Detailed results
            if results['query_results']:
                st.subheader("📋 Detailed Results")

                results_df = pd.DataFrame(results['query_results'])
                st.dataframe(results_df)

                # Download results
                csv = results_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Results CSV",
                    data=csv,
                    file_name=f"evaluation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )

        except Exception as e:
            st.error(f"Evaluation failed: {str(e)}")

def save_session_data():
    """Save current session data"""
    session_data = {
        'query_history': st.session_state.query_history,
        'playbook_summary': st.session_state.ace_instance.get_playbook_summary() if st.session_state.ace_instance else None,
        'statistics': st.session_state.ace_instance.get_statistics() if st.session_state.ace_instance else None,
        'timestamp': datetime.now().isoformat()
    }

    json_str = json.dumps(session_data, indent=2, default=str)

    # Create download
    b64 = base64.b64encode(json_str.encode()).decode()
    href = f'<a href="data:file/json;base64,{b64}" download="ace_session_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json">Download Session Data</a>'
    st.markdown(href, unsafe_allow_html=True)
    st.success("Session data ready for download!")

def main():
    """Main application function"""
    # Initialize session state
    init_session_state()

    # Render header
    render_header()

    # Render sidebar and get selected page
    page = render_sidebar()

    # Render selected page
    if page == "🏠 Dashboard":
        render_dashboard_overview()
    elif page == "💬 Q&A Interface":
        render_qa_interface()
    elif page == "🔧 MCP Tools Manager":
        render_mcp_tools_manager()
    elif page == "📚 Playbook Manager":
        render_playbook_manager()
    elif page == "📊 Statistics":
        render_statistics()
    elif page == "⚙️ Configuration":
        render_configuration()
    elif page == "🧪 Batch Processing":
        render_batch_processing()

    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666;'>"
        "🧠 ACE Framework Dashboard - Built with Streamlit"
        "</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()