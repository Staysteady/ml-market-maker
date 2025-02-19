import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

API_BASE_URL = "http://localhost:8000"

def create_metric_chart(data: list, metric_name: str, title: str) -> go.Figure:
    """Create a time series chart for a metric."""
    df = pd.DataFrame(data)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df[metric_name],
        mode='lines+markers',
        name=metric_name
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Time",
        yaxis_title="Value",
        height=400
    )
    
    return fig

def main():
    """Monitoring page."""
    st.set_page_config(
        page_title="Model Monitoring",
        page_icon="📈",
        layout="wide"
    )
    
    st.title("Model Monitoring")
    
    # Time range selector
    time_ranges = {
        "Last Hour": 1,
        "Last 6 Hours": 6,
        "Last 24 Hours": 24,
        "Last 7 Days": 24 * 7
    }
    
    selected_range = st.selectbox(
        "Time Range",
        options=list(time_ranges.keys())
    )
    
    try:
        # Get metrics
        response = requests.get(
            f"{API_BASE_URL}/metrics",
            params={'window_hours': time_ranges[selected_range]}
        )
        metrics = response.json()
        
        # Performance Metrics
        st.header("Performance Metrics")
        
        # Create performance charts
        perf_metrics = metrics['performance']
        col1, col2 = st.columns(2)
        
        with col1:
            latency_chart = create_metric_chart(
                perf_metrics['history'],
                'latency_ms',
                'Prediction Latency'
            )
            st.plotly_chart(latency_chart, use_container_width=True)
            
            throughput_chart = create_metric_chart(
                perf_metrics['history'],
                'throughput',
                'Prediction Throughput'
            )
            st.plotly_chart(throughput_chart, use_container_width=True)
            
        with col2:
            error_chart = create_metric_chart(
                perf_metrics['history'],
                'error_rate',
                'Error Rate'
            )
            st.plotly_chart(error_chart, use_container_width=True)
            
            accuracy_chart = create_metric_chart(
                perf_metrics['history'],
                'accuracy',
                'Prediction Accuracy'
            )
            st.plotly_chart(accuracy_chart, use_container_width=True)
            
        # System Health
        st.header("System Health")
        
        # Create health charts
        health_metrics = metrics['health']
        col1, col2 = st.columns(2)
        
        with col1:
            memory_chart = create_metric_chart(
                health_metrics['history'],
                'memory_usage',
                'Memory Usage (MB)'
            )
            st.plotly_chart(memory_chart, use_container_width=True)
            
        with col2:
            cpu_chart = create_metric_chart(
                health_metrics['history'],
                'cpu_usage',
                'CPU Usage (%)'
            )
            st.plotly_chart(cpu_chart, use_container_width=True)
            
        # Alerts History
        st.header("Alerts History")
        if metrics['alerts']:
            for alert in metrics['alerts']:
                st.warning(alert)
        else:
            st.success("No active alerts")
            
    except Exception as e:
        st.error(f"Error fetching metrics: {str(e)}")

if __name__ == "__main__":
    main() 