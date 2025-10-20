"""
Streamlit Utilities for ACE Framework
Additional utilities and visualization helpers for the Streamlit interface
"""
import streamlit as st
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

# Try to import optional dependencies
try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False

# Import ACE models
from ace.models import Bullet, Playbook, Trajectory, BulletType, BulletTag

def create_bullet_network_visualization(playbook: Playbook, max_nodes: int = 50):
    """Create a network visualization of bullet connections"""
    if not NETWORKX_AVAILABLE or not PLOTLY_AVAILABLE:
        st.warning("⚠️ Network visualization requires 'networkx' and 'plotly' packages")
        return None

    if not playbook.bullets:
        return None

    # Create a graph
    G = nx.Graph()

    # Add nodes (bullets)
    bullets_to_show = playbook.bullets[:max_nodes]
    for i, bullet in enumerate(bullets_to_show):
        G.add_node(
            bullet.id,
            label=bullet.content[:30] + "...",
            type=bullet.bullet_type.value,
            section=bullet.section,
            tag=bullet.tag().value,
            helpfulness=bullet.helpful_count - bullet.harmful_count
        )

    # Create edges based on shared keywords or sections
    for i, bullet1 in enumerate(bullets_to_show):
        for j, bullet2 in enumerate(bullets_to_show[i+1:], i+1):
            # Connect bullets from same section
            if bullet1.section == bullet2.section:
                G.add_edge(bullet1.id, bullet2.id, weight=2, type="same_section")

            # Connect bullets with similar content keywords
            words1 = set(bullet1.content.lower().split())
            words2 = set(bullet2.content.lower().split())
            common_words = words1.intersection(words2)

            if len(common_words) > 2:  # More than 2 common words
                G.add_edge(bullet1.id, bullet2.id, weight=1, type="similar_content")

    if len(G.nodes()) == 0:
        return None

    # Calculate layout
    pos = nx.spring_layout(G, k=1, iterations=50)

    # Create plotly traces
    node_trace = go.Scatter(
        x=[],
        y=[],
        mode='markers+text',
        text=[],
        textposition="middle center",
        hoverinfo='text',
        marker=dict(
            size=[],
            color=[],
            colorscale='RdYlGn',
            showscale=True,
            colorbar=dict(title="Helpfulness")
        )
    )

    edge_trace = go.Scatter(
        x=[],
        y=[],
        mode='lines',
        line=dict(width=0.5, color='#888'),
        hoverinfo='none'
    )

    # Add edges
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_trace['x'] += (x0, x1, None)
        edge_trace['y'] += (y0, y1, None)

    # Add nodes
    for node in G.nodes():
        x, y = pos[node]
        node_trace['x'] += (x,)
        node_trace['y'] += (y,)

        node_data = G.nodes[node]
        node_trace['text'] += (node_data['label'],)
        node_trace['marker']['size'] += (10 + node_data['helpfulness'],)
        node_trace['marker']['color'] += (node_data['helpfulness'],)

    # Create figure
    fig = go.Figure()
    fig.add_trace(edge_trace)
    fig.add_trace(node_trace)

    fig.update_layout(
        title='Bullet Knowledge Network',
        title_font_size=16,
        showlegend=False,
        hovermode='closest',
        margin=dict(b=20, l=5, r=5, t=40),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
    )

    return fig

def create_trajectory_timeline(trajectories: List[Trajectory]):
    """Create a timeline visualization of trajectories"""
    if not PLOTLY_AVAILABLE or not PANDAS_AVAILABLE:
        st.warning("⚠️ Timeline visualization requires 'plotly' and 'pandas' packages")
        return None

    if not trajectories:
        return None

    # Prepare data
    df_data = []
    for traj in trajectories:
        df_data.append({
            'id': traj.id[:8],
            'query': traj.query[:50] + "...",
            'success': traj.success,
            'timestamp': traj.created_at,
            'code_length': len(traj.generated_code) if traj.generated_code else 0,
            'error': bool(traj.error_message)
        })

    df = pd.DataFrame(df_data)

    # Create timeline
    fig = px.scatter(
        df,
        x='timestamp',
        y=[1] * len(df),  # All on same line
        color='success',
        symbol='error',
        size='code_length',
        hover_data=['query'],
        title="Query Execution Timeline",
        color_discrete_map={True: 'green', False: 'red'}
    )

    fig.update_layout(
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        xaxis_title="Time",
        height=200
    )

    fig.update_traces(marker=dict(line=dict(width=2, color='DarkSlateGrey')))

    return fig

def create_playbook_evolution_chart(playbook_data: List[Dict]):
    """Create a chart showing playbook evolution over time"""
    if not playbook_data:
        return None

    df = pd.DataFrame(playbook_data)

    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Bullet Count Over Time', 'Success Rate Over Time'),
        vertical_spacing=0.1
    )

    # Bullet count
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'],
            y=df['bullet_count'],
            mode='lines+markers',
            name='Total Bullets',
            line=dict(color='blue')
        ),
        row=1, col=1
    )

    # Success rate
    if 'success_rate' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['success_rate'],
                mode='lines+markers',
                name='Success Rate',
                line=dict(color='green')
            ),
            row=2, col=1
        )

    fig.update_layout(
        title="Playbook Evolution",
        height=500
    )

    return fig

def create_bullet_type_distribution(playbook: Playbook):
    """Create a distribution chart of bullet types"""
    if not playbook.bullets:
        return None

    # Count bullet types
    type_counts = {}
    section_counts = {}
    tag_counts = {}

    for bullet in playbook.bullets:
        # Type counts
        bullet_type = bullet.bullet_type.value
        type_counts[bullet_type] = type_counts.get(bullet_type, 0) + 1

        # Section counts
        section = bullet.section
        section_counts[section] = section_counts.get(section, 0) + 1

        # Tag counts
        tag = bullet.tag().value
        tag_counts[tag] = tag_counts.get(tag, 0) + 1

    # Create subplots
    fig = make_subplots(
        rows=1, cols=3,
        specs=[[{"type": "domain"}, {"type": "domain"}, {"type": "domain"}]],
        subplot_titles=('Bullet Types', 'Sections', 'Tags')
    )

    # Add pie charts
    fig.add_trace(
        go.Pie(labels=list(type_counts.keys()), values=list(type_counts.values()), name="Types"),
        row=1, col=1
    )

    fig.add_trace(
        go.Pie(labels=list(section_counts.keys()), values=list(section_counts.values()), name="Sections"),
        row=1, col=2
    )

    fig.add_trace(
        go.Pie(labels=list(tag_counts.keys()), values=list(tag_counts.values()), name="Tags"),
        row=1, col=3
    )

    fig.update_layout(
        title="Playbook Composition Analysis",
        height=400
    )

    return fig

def create_performance_metrics(stats: Dict[str, Any]):
    """Create performance metrics visualization"""
    if not stats:
        return None

    # Create metrics data
    metrics_data = [
        {'Metric': 'Success Rate', 'Value': stats.get('success_rate', 0) * 100, 'Unit': '%'},
        {'Metric': 'Total Trajectories', 'Value': stats.get('total_trajectories', 0), 'Unit': ''},
        {'Metric': 'Playbook Size', 'Value': stats.get('playbook_size', 0), 'Unit': 'bullets'},
        {'Metric': 'Delta Updates', 'Value': stats.get('total_delta_updates', 0), 'Unit': ''}
    ]

    df = pd.DataFrame(metrics_data)

    # Create bar chart
    fig = px.bar(
        df,
        x='Metric',
        y='Value',
        title="Performance Metrics",
        text='Value'
    )

    fig.update_layout(
        yaxis_title="Value",
        xaxis_title="Metric"
    )

    fig.update_traces(texttemplate='%{text} %{text2}', textposition='outside')

    return fig

def create_query_analysis_dashboard(query_history: List[Dict]):
    """Create comprehensive query analysis dashboard"""
    if not query_history:
        return None

    df = pd.DataFrame(query_history)
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Queries Over Time', 'Success Rate Trend', 'Query Length Distribution', 'Hourly Activity'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )

    # Queries over time
    daily_counts = df.groupby(df['timestamp'].dt.date).size()
    fig.add_trace(
        go.Scatter(
            x=daily_counts.index,
            y=daily_counts.values,
            mode='lines+markers',
            name='Daily Queries'
        ),
        row=1, col=1
    )

    # Success rate trend
    df_sorted = df.sort_values('timestamp')
    df_sorted['rolling_success'] = df_sorted['success'].rolling(window=min(10, len(df_sorted)), min_periods=1).mean()
    fig.add_trace(
        go.Scatter(
            x=df_sorted['timestamp'],
            y=df_sorted['rolling_success'],
            mode='lines',
            name='Rolling Success Rate',
            line=dict(color='green')
        ),
        row=1, col=2
    )

    # Query length distribution
    if 'query' in df.columns:
        df['query_length'] = df['query'].str.len()
        fig.add_trace(
            go.Histogram(
                x=df['query_length'],
                nbinsx=20,
                name='Query Length'
            ),
            row=2, col=1
        )

    # Hourly activity
    df['hour'] = df['timestamp'].dt.hour
    hourly_counts = df['hour'].value_counts().sort_index()
    fig.add_trace(
        go.Bar(
            x=hourly_counts.index,
            y=hourly_counts.values,
            name='Hourly Queries'
        ),
        row=2, col=2
    )

    fig.update_layout(
        title="Query Analysis Dashboard",
        height=600,
        showlegend=False
    )

    return fig

def display_trajectory_details(trajectory: Trajectory):
    """Display detailed trajectory information in a formatted way"""
    if not trajectory:
        st.warning("No trajectory data available")
        return

    # Header
    status_emoji = "✅" if trajectory.success else "❌"
    st.subheader(f"{status_emoji} Trajectory Details")

    # Main info
    col1, col2 = st.columns(2)

    with col1:
        st.write("**Query:**")
        st.write(trajectory.query)

        st.write("**Status:**")
        st.write("Success" if trajectory.success else "Failed")

        st.write("**Created:**")
        st.write(trajectory.created_at.strftime("%Y-%m-%d %H:%M:%S"))

    with col2:
        if trajectory.generated_code:
            st.write("**Code Length:**")
            st.write(f"{len(trajectory.generated_code)} characters")

        if trajectory.used_bullet_ids:
            st.write("**Bullets Used:**")
            st.write(f"{len(trajectory.used_bullet_ids)} bullets")

        if trajectory.metadata:
            st.write("**Metadata:**")
            st.json(trajectory.metadata)

    # Tabs for different sections
    tab1, tab2, tab3, tab4 = st.tabs(["🧠 Reasoning", "💻 Code", "🏃 Execution", "📊 Metadata"])

    with tab1:
        if trajectory.reasoning_steps:
            st.write("**Reasoning Steps:**")
            for i, step in enumerate(trajectory.reasoning_steps, 1):
                with st.expander(f"Step {i}"):
                    st.write(step)
        else:
            st.info("No reasoning steps recorded")

    with tab2:
        if trajectory.generated_code:
            st.code(trajectory.generated_code, language='python')
        else:
            st.info("No code generated")

    with tab3:
        if trajectory.execution_result:
            st.write("**Execution Result:**")
            st.text(trajectory.execution_result)
        else:
            st.info("No execution result")

        if trajectory.error_message:
            st.write("**Error Message:**")
            st.error(trajectory.error_message)

    with tab4:
        if trajectory.metadata:
            st.json(trajectory.metadata)
        else:
            st.info("No metadata available")

def display_reflection_details(reflection):
    """Display detailed reflection information"""
    if not reflection:
        st.warning("No reflection data available")
        return

    st.subheader("🔍 Reflection Analysis")

    # Main content
    if reflection.reasoning:
        st.write("**Analysis:**")
        st.write(reflection.reasoning)

    if reflection.error_identification:
        st.write("**Error Identification:**")
        st.warning(reflection.error_identification)

    if reflection.root_cause_analysis:
        st.write("**Root Cause Analysis:**")
        st.info(reflection.root_cause_analysis)

    if reflection.correct_approach:
        st.write("**Correct Approach:**")
        st.success(reflection.correct_approach)

    if reflection.key_insight:
        st.write("**Key Insight:**")
        st.markdown(f"> 💡 {reflection.key_insight}")

    if reflection.bullet_tags:
        st.write("**Bullet Updates:**")
        for bullet_id, tag in reflection.bullet_tags.items():
            st.write(f"• Bullet {bullet_id[:8]}... → {tag.value}")

def export_session_data(session_state, filename_prefix="ace_session"):
    """Export session data as JSON"""
    export_data = {
        'timestamp': datetime.now().isoformat(),
        'query_history': session_state.get('query_history', []),
        'playbook_summary': None,
        'statistics': None,
        'config_loaded': session_state.get('config_loaded', False)
    }

    # Add playbook data if available
    if session_state.get('ace_instance'):
        try:
            export_data['playbook_summary'] = session_state.ace_instance.get_playbook_summary()
            export_data['statistics'] = session_state.ace_instance.get_statistics()
        except Exception as e:
            st.warning(f"Could not export playbook data: {str(e)}")

    return json.dumps(export_data, indent=2, default=str)

def create_bullet_heatmap(playbook: Playbook):
    """Create a heatmap showing bullet interactions by section and type"""
    if not PLOTLY_AVAILABLE:
        st.warning("⚠️ Heatmap visualization requires 'plotly' package")
        return None

    if not playbook.bullets:
        return None

    # Create matrix data
    sections = list(set(bullet.section for bullet in playbook.bullets))
    types = list(set(bullet.bullet_type.value for bullet in playbook.bullets))

    # Initialize matrix
    matrix = [[0] * len(types) for _ in range(len(sections))]

    # Count bullets
    for bullet in playbook.bullets:
        section_idx = sections.index(bullet.section)
        type_idx = types.index(bullet.bullet_type.value)
        matrix[section_idx][type_idx] += 1

    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=types,
        y=sections,
        colorscale='Blues',
        hoverongaps=False
    ))

    fig.update_layout(
        title="Bullet Distribution Heatmap (Section vs Type)",
        xaxis_title="Bullet Type",
        yaxis_title="Section"
    )

    return fig