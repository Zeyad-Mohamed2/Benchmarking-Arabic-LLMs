import argparse
import sys
import uvicorn
from benchmark_arabic_llms.app.streamlit_benchmark_app import StreamlitBenchmarkApp
from benchmark_arabic_llms.api.main import app as fastapi_app


def run_streamlit():
    """Run Streamlit app."""
    # Use sys.argv simulation to run streamlit from script
    import streamlit.web.cli as stcli
    import os
    
    script_path = os.path.abspath(__file__)
    sys.argv = ["streamlit", "run", script_path, "--server.port=8501"]
    sys.exit(stcli.main())

def run_api(host: str = "0.0.0.0", port: int = 8000):
    """Run FastAPI server."""
    uvicorn.run(fastapi_app, host=host, port=port)

def main():
    """Main entry point for application."""
    # When Streamlit runs this file, it sets its own internal state
    # We can detect this by checking if Streamlit is already running
    import streamlit.runtime.scriptrunner as scriptrunner
    
    # Check if we're running inside a Streamlit context
    try:
        is_streamlit = scriptrunner.get_script_run_ctx() is not None
    except Exception:
        is_streamlit = False

    if is_streamlit:
        import streamlit as st
        from PIL import Image
        
        # We are exactly inside streamlit run
        logo_left = Image.open("assets/Fayoum University Logo.jpeg")
        logo_right = Image.open("assets/FCAI Fayoum University Logo.jpeg")
        st.set_page_config(
            page_title="Framework for Open-Source Multilingual Large Language Models",
            page_icon=logo_left,
            layout="wide",
        )

        st.markdown(
            """
                <style>
                    .block-container {
                        padding-top: 3.7rem;
                    }
                    [data-testid="stAppDeployButton"] {display: none;}
                    div.stButton > button[kind="primary"],
                    div.stDownloadButton > button[kind="primary"] {
                        background-color: #32C4B7;
                        border-color: #32C4B7;
                    }
                    div.stButton > button[kind="primary"]:hover,
                    div.stDownloadButton > button[kind="primary"]:hover {
                        background-color: #2aa69b;
                        border-color: #2aa69b;
                    }
                </style>
                """,
            unsafe_allow_html=True,
        )

        col1, col2, col3 = st.columns([1, 4, 1])
        with col1:
            st.image(logo_left, width=100)
        with col3:
            st.image(logo_right, width=120)

        app = StreamlitBenchmarkApp()
        app.run()
        return

    # CLI Argument parsing
    parser = argparse.ArgumentParser(description="Run Benchmark Arabic LLMs Application")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["api", "ui"],
        default="ui",
        help="Run mode: 'api' for FastAPI backend, 'ui' for Streamlit frontend"
    )
    parser.add_argument("--port", type=int, default=8081, help="Port to run API on (if in api mode)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to run API on (if in api mode)")

    args = parser.parse_args()

    if args.mode == "api":
        print(f"Starting API Server on {args.host}:{args.port}")
        run_api(host=args.host, port=args.port)
    elif args.mode == "ui":
        print("Starting Streamlit Application...")
        run_streamlit()


if __name__ == "__main__":
    main()

