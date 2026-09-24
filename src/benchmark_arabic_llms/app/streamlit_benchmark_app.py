"""
This file defines the StreamlitBenchmarkApp, a Streamlit-based interface for running Arabic LLM benchmarks.
It allows users to configure tasks, models, datasets, and semantic matching, while visualizing progress and displaying detailed benchmark results.
"""

import os
import streamlit as st
from PIL import Image
from pathlib import Path
from dotenv import load_dotenv
from typing import Any, Dict, Optional
import pandas as pd
from benchmark_arabic_llms.core.enums import BenchmarkTask
from benchmark_arabic_llms.config.data_paths import LOGS_DIR, EXCEL_DIR
from benchmark_arabic_llms.app.benchmark_orchestrator import BenchmarkOrchestrator
from google import genai
from benchmark_arabic_llms.services.llm_client import OpenRouterClient, GroqClient
from benchmark_arabic_llms.core.exceptions import (
    ClientError,
    RateLimitError,
    PaymentError,
    TokenLimitError,
    TimeoutError,
)


class StreamlitBenchmarkApp:
    """Streamlit application for running benchmarks."""

    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.orchestrator = BenchmarkOrchestrator(LOGS_DIR, EXCEL_DIR)

        # Initialize session state variables
        if "custom_prompt" not in st.session_state:
            st.session_state.custom_prompt = None
        if "use_semantic_matching" not in st.session_state:
            st.session_state.use_semantic_matching = False
        if "uploaded_dataset" not in st.session_state:
            st.session_state.uploaded_dataset = None
        if "gemini_connection_status" not in st.session_state:
            st.session_state.gemini_connection_status = None
        if "openrouter_connection_status" not in st.session_state:
            st.session_state.openrouter_connection_status = None
        if "groq_connection_status" not in st.session_state:
            st.session_state.groq_connection_status = None
        if "last_results" not in st.session_state:
            st.session_state.last_results = None
        if "selected_models" not in st.session_state:
            st.session_state.selected_models = []
        if "provider" not in st.session_state:
            st.session_state.provider = "openrouter"
        if "enable_checkpoint_mode" not in st.session_state:
            st.session_state.enable_checkpoint_mode = False
        if "checkpoint_interval" not in st.session_state:
            st.session_state.checkpoint_interval = 50

    def run(self):
        """Run the Streamlit application."""

        st.markdown(
            "<h1 style='font-size: 2.2rem;'>Framework for Open-Source Multilingual Large Language Models</h1>",
            unsafe_allow_html=True,
        )
        st.markdown("---")

        self._render_sidebar()
        self._render_main_content()

    def _test_gemini_connection(
        self, api_key: str, model_name: str
    ) -> tuple[bool, str]:
        """Test Gemini API connection without saving the key."""
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=model_name,
                contents="Test"
            )
            return True, "✅ Connection successful"
        except Exception as e:
            error_msg = str(e)
            if "API_KEY_INVALID" in error_msg or "invalid" in error_msg.lower():
                return False, "❌ [Auth Error] Invalid API key"
            elif "quota" in error_msg.lower() or "billing" in error_msg.lower():
                return False, "❌ [Payment/Quota Error] Quota exceeded or billing issue"
            elif "not found" in error_msg.lower():
                return False, "❌ [Not Found] Model not found"
            else:
                return False, f"❌ Connection failed: {error_msg[:50]}"

    def _test_openrouter_connection(
        self, api_key: str, model_name: str
    ) -> tuple[bool, str]:
        """Test OpenRouter API connection without saving the key."""
        try:
            client = OpenRouterClient(api_key=api_key, model=model_name)
            client.generate("Test", temperature=0.0)
            return True, "✅ Connection successful"
        except RateLimitError as e:
            return False, "❌ [Rate Limit] Too many requests - please wait and retry"
        except PaymentError as e:
            return False, "❌ [Payment Error] Billing or quota issue - check your account"
        except TokenLimitError as e:
            return False, "❌ [Token Limit] Request exceeds token limits"
        except TimeoutError as e:
            return False, "❌ [Timeout] Request timed out - check your connection"
        except ClientError as e:
            error_type = e.error_type.replace("_", " ").title()
            return False, f"❌ [{error_type}] {str(e)[:50]}"
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "unauthorized" in error_msg.lower():
                return False, "❌ [Auth Error] Invalid API key"
            elif "404" in error_msg or "not found" in error_msg.lower():
                return False, "❌ [Not Found] Model not found"
            else:
                return False, f"❌ Connection failed: {error_msg[:50]}"

    def _test_groq_connection(self, api_key: str, model_name: str) -> tuple[bool, str]:
        """Test Groq API connection without saving the key."""
        try:
            client = GroqClient(api_key=api_key, model=model_name)
            client.generate("Test", temperature=0.0)
            return True, "✅ Connection successful"
        except RateLimitError as e:
            return False, "❌ [Rate Limit] Too many requests - please wait and retry"
        except PaymentError as e:
            return False, "❌ [Payment Error] Billing or quota issue - check your account"
        except TokenLimitError as e:
            return False, "❌ [Token Limit] Request exceeds token limits"
        except TimeoutError as e:
            return False, "❌ [Timeout] Request timed out - check your connection"
        except ClientError as e:
            error_type = e.error_type.replace("_", " ").title()
            return False, f"❌ [{error_type}] {str(e)[:50]}"
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "unauthorized" in error_msg.lower():
                return False, "❌ [Auth Error] Invalid API key"
            elif "404" in error_msg or "not found" in error_msg.lower():
                return False, "❌ [Not Found] Model not found"
            else:
                return False, f"❌ Connection failed: {error_msg[:50]}"

    def _render_sidebar(self):
        """Render sidebar configuration."""
        st.sidebar.header("Benchmarking Configuration")

        # Task selection
        self.selected_task = st.sidebar.selectbox(
            "Select Case:",
            BenchmarkTask.get_all(),
            help="Choose the type of benchmark to run",
        )

        # Model Provider Configuration Section
        st.sidebar.markdown("---")
        st.sidebar.subheader("Model Provider")

        # Provider selection
        st.session_state.provider = st.sidebar.radio(
            "Select Provider",
            ["openrouter", "groq"],
            format_func=lambda x: "OpenRouter" if x == "openrouter" else "Groq",
            horizontal=True,
        )

        # Multi-model selection (up to 3 models)
        self.selected_models = self._render_multi_model_selection()

        if st.session_state.provider == "openrouter":
            # OpenRouter API Key input
            openrouter_api_input = st.sidebar.text_input(
                "OpenRouter API Key",
                type="password",
                value=self.api_key or "",
                help="Enter your OpenRouter API key (not saved)",
                placeholder="Enter API key...",
                key="openrouter_api_key",
            )

            # Update the active API key (in memory only)
            if openrouter_api_input:
                self.api_key = openrouter_api_input

            # Test OpenRouter connection button
            if st.sidebar.button("🔌 Test Connection", key="test_openrouter"):
                if not self.api_key:
                    st.sidebar.error("⚠️ Please enter an API key")
                    st.session_state.openrouter_connection_status = None
                elif not self.selected_models:
                    st.sidebar.error("⚠️ Please select at least one model")
                    st.session_state.openrouter_connection_status = None
                else:
                    with st.spinner("Testing OpenRouter connection..."):
                        # Test all selected models
                        all_success = True
                        messages = []
                        for model in self.selected_models:
                            success, message = self._test_openrouter_connection(
                                self.api_key, model
                            )
                            messages.append(f"**{model}**: {message}")
                            if not success:
                                all_success = False

                        st.session_state.openrouter_connection_status = (
                            all_success,
                            messages,
                        )

            # Display OpenRouter connection status
            if st.session_state.openrouter_connection_status:
                success, messages = st.session_state.openrouter_connection_status
                if success:
                    st.sidebar.success("✅ All models connected successfully")
                    for message in messages:
                        st.sidebar.caption(message)
                else:
                    st.sidebar.error("❌ One or more models failed to connect")
                    for message in messages:
                        st.sidebar.caption(message)
            elif not self.api_key:
                st.sidebar.warning("⚠️ No API key provided")

        elif st.session_state.provider == "groq":
            # Groq API Key input
            groq_api_input = st.sidebar.text_input(
                "Groq API Key",
                type="password",
                value=self.groq_api_key or "",
                help="Enter your Groq API key (not saved)",
                placeholder="Enter API key...",
                key="groq_api_key",
            )

            # Update the active API key (in memory only)
            if groq_api_input:
                self.groq_api_key = groq_api_input

            # Test Groq connection button
            if st.sidebar.button("🔌 Test Connection", key="test_groq"):
                if not self.groq_api_key:
                    st.sidebar.error("⚠️ Please enter an API key")
                    st.session_state.groq_connection_status = None
                elif not self.selected_models:
                    st.sidebar.error("⚠️ Please select at least one model")
                    st.session_state.groq_connection_status = None
                else:
                    with st.spinner("Testing Groq connection..."):
                        # Test all selected models
                        all_success = True
                        messages = []
                        for model in self.selected_models:
                            success, message = self._test_groq_connection(
                                self.groq_api_key, model
                            )
                            messages.append(f"**{model}**: {message}")
                            if not success:
                                all_success = False

                        st.session_state.groq_connection_status = (
                            all_success,
                            messages,
                        )

            # Display Groq connection status
            if st.session_state.groq_connection_status:
                success, messages = st.session_state.groq_connection_status
                if success:
                    st.sidebar.success("✅ All models connected successfully")
                    for message in messages:
                        st.sidebar.caption(message)
                else:
                    st.sidebar.error("❌ One or more models failed to connect")
                    for message in messages:
                        st.sidebar.caption(message)
            elif not self.groq_api_key:
                st.sidebar.warning("⚠️ No API key provided")

        # Dataset upload section
        st.sidebar.markdown("---")
        st.sidebar.subheader("📁 Dataset")

        uploaded_file = st.sidebar.file_uploader(
            "Upload Custom Dataset (Optional) ",
            type=["csv", "xlsx"],
            help="Upload your own dataset or use the default dataset",
        )

        if uploaded_file is not None:
            st.session_state.uploaded_dataset = uploaded_file
            st.sidebar.success(f"✓ Uploaded: {uploaded_file.name}")

            # Show required columns based on selected task
            if self.selected_task:
                required_cols = self._get_required_columns(self.selected_task)
                st.sidebar.info(f"📋 Required columns: {', '.join(required_cols)}")
        else:
            st.session_state.uploaded_dataset = None
            st.sidebar.warning("Using default dataset")

        # Number of samples
        st.sidebar.markdown("---")
        self.number_of_samples = st.sidebar.number_input(
            "Number of Samples",
            min_value=1,
            step=1,
            value=1,
            help="Select how many samples to run",
        )

        # Checkpoint Mode
        st.sidebar.markdown("---")
        st.sidebar.subheader("💾 Checkpoint Mode")

        self.enable_checkpoint_mode = st.sidebar.checkbox(
            "Enable Checkpoint Mode",
            value=st.session_state.enable_checkpoint_mode,
            help="Save progress every N samples to resume if interrupted",
            key="enable_checkpoint_mode"
        )

        if self.enable_checkpoint_mode:
            self.checkpoint_interval = st.sidebar.number_input(
                "Save Every N Samples",
                min_value=10,
                max_value=500,
                value=st.session_state.checkpoint_interval,
                step=10,
                help="Checkpoint interval (smaller = safer, but more disk writes)",
                key="checkpoint_interval"
            )
            
            st.sidebar.info(
                "✓ Progress saved incrementally\n"
                "✓ Resume automatically if interrupted\n"
                "✓ Partial results available in Excel"
            )
        else:
            self.checkpoint_interval = 50  # Default, won't be used

        # Semantic matching option
        st.sidebar.markdown("---")
        st.sidebar.subheader("🧠 LLM as a Judge (Gemini)")

        # Disable semantic matching for sarcasm task
        is_sarcasm_task = self.selected_task and self.selected_task.lower() == "sarcasm"

        if is_sarcasm_task:
            st.sidebar.info(
                "ℹ️ Semantic matching is not available for Sarcasm Detection task"
            )
            self.use_semantic_matching = False
        else:
            self.use_semantic_matching = st.sidebar.checkbox(
                "Semantic Matching",
                value=False,
                help="Use Gemini to evaluate semantic match (beyond token matching)",
            )

        if self.use_semantic_matching:
            # Gemini model selection
            gemini_models = [
                "gemini-2.5-flash",
                "gemini-2.5-flash-lite",
                "gemini-2.5-pro",
                "gemini-2.0-flash",
                "gemini-2.0-flash-lite",
                "gemini-2.0-pro",
            ]

            self.selected_gemini_model = st.sidebar.selectbox(
                "Gemini Model",
                gemini_models,
                index=1,  # Default to gemini-2.5-flash-lite
                help="Select the Gemini model for semantic evaluation",
            )

            # Gemini API Key input
            gemini_api_input = st.sidebar.text_input(
                "Gemini API Key",
                type="password",
                value=self.gemini_api_key or "",
                help="Enter your Google Gemini API key (not saved)",
                placeholder="Enter API key...",
                key="gemini_api_key",
            )

            # Update the active API key (in memory only)
            if gemini_api_input:
                self.gemini_api_key = gemini_api_input

            # Test Gemini connection button
            if st.sidebar.button("🔌 Test Connection", key="test_gemini"):
                if not self.gemini_api_key:
                    st.sidebar.error("⚠️ Please enter a Gemini API key")
                    st.session_state.gemini_connection_status = None
                else:
                    with st.spinner("Testing Gemini connection..."):
                        success, message = self._test_gemini_connection(
                            self.gemini_api_key, self.selected_gemini_model
                        )
                        st.session_state.gemini_connection_status = (success, message)

            # Display Gemini connection status
            if st.session_state.gemini_connection_status:
                success, message = st.session_state.gemini_connection_status
                if success:
                    st.sidebar.success(message)
                else:
                    st.sidebar.error(message)
            elif not self.gemini_api_key:
                st.sidebar.warning("⚠️ No Gemini API key provided")

    def _get_required_columns(self, task: str) -> list:
        """Get required columns for a given task."""
        column_map = {
            "summarization": ["text", "summary"],
            "question_answering": ["text", "question", "answer"],
            "sarcasm": ["text", "sarcasm"],
        }
        return column_map.get(task.lower(), [])

    def _get_openrouter_model_options(self) -> Dict[str, str]:
        """Get OpenRouter model options mapping display name to API ID."""
        return {
            "Google Gemma 3 27B IT": "google/gemma-3-27b-it:free",
            "OpenAI GPT-OSS 20B": "openai/gpt-oss-20b:free",
            "Qwen 3 4B": "qwen/qwen3-4b:free",
            "Cohere Command R7B": "cohere/command-r7b-12-2024",
            "Meta Llama 3.3 70B Instruct": "meta-llama/llama-3.3-70b-instruct:free",
            "Other (custom)": "Other (custom)",
        }

    def _get_groq_model_options(self) -> Dict[str, str]:
        """Get Groq model options mapping display name to API ID."""
        return {
            "OpenAI GPT-OSS 20B": "openai/gpt-oss-20b",
            "Qwen 3 32B": "qwen/qwen3-32b",
            "Llama 4 Maverick 17B 128E": "meta-llama/llama-4-maverick-17b-128e-instruct",
            "Kimi K2 0905": "moonshotai/kimi-k2-instruct-0905",
            "Other (custom)": "Other (custom)",
        }

    def _render_multi_model_selection(self) -> list:
        """Render multi-model selection interface (up to 3 models)."""
        if st.session_state.provider == "groq":
            model_options = self._get_groq_model_options()
        else:
            model_options = self._get_openrouter_model_options()
        display_names = list(model_options.keys())

        st.sidebar.write("**Select up to 3 models**")

        selected_models = []

        # First model
        model1_display = st.sidebar.selectbox(
            "Model 1",
            display_names,
            key="model_1_select",
            help="Select the first model for comparison",
        )

        if model1_display == "Other (custom)":
            model1_custom = st.sidebar.text_input(
                "Custom Model 1",
                value="",
                help="Enter a custom model identifier",
                key="model_1_custom",
            )
            if model1_custom.strip():
                selected_models.append(model1_custom.strip())
        else:
            selected_models.append(model_options[model1_display])

        # Second model (optional)
        add_model2 = st.sidebar.checkbox(
            "Add second model", value=False, key="add_model2"
        )
        if add_model2:
            model2_display = st.sidebar.selectbox(
                "Model 2",
                display_names,
                key="model_2_select",
                help="Select the second model for comparison",
            )

            if model2_display == "Other (custom)":
                model2_custom = st.sidebar.text_input(
                    "Custom Model 2",
                    value="",
                    help="Enter a custom model identifier",
                    key="model_2_custom",
                )
                if model2_custom.strip():
                    selected_models.append(model2_custom.strip())
            else:
                model2_id = model_options[model2_display]
                if model2_id not in selected_models:  # Avoid duplicates
                    selected_models.append(model2_id)

        # Third model (optional)
        add_model3 = st.sidebar.checkbox(
            "Add third model", value=False, key="add_model3"
        )
        if add_model3:
            model3_display = st.sidebar.selectbox(
                "Model 3",
                display_names,
                key="model_3_select",
                help="Select the third model for comparison",
            )

            if model3_display == "Other (custom)":
                model3_custom = st.sidebar.text_input(
                    "Custom Model 3",
                    value="",
                    help="Enter a custom model identifier",
                    key="model_3_custom",
                )
                if model3_custom.strip():
                    selected_models.append(model3_custom.strip())
            else:
                model3_id = model_options[model3_display]
                if model3_id not in selected_models:  # Avoid duplicates
                    selected_models.append(model3_id)

        # Fourth model (optional)
        add_model4 = st.sidebar.checkbox(
            "Add fourth model", value=False, key="add_model4"
        )
        if add_model4:
            model4_display = st.sidebar.selectbox(
                "Model 4",
                display_names,
                key="model_4_select",
                help="Select the fourth model for comparison",
            )

            if model4_display == "Other (custom)":
                model4_custom = st.sidebar.text_input(
                    "Custom Model 4",
                    value="",
                    help="Enter a custom model identifier",
                    key="model_4_custom",
                )
                if model4_custom.strip():
                    selected_models.append(model4_custom.strip())
            else:
                model4_id = model_options[model4_display]
                if model4_id not in selected_models:  # Avoid duplicates
                    selected_models.append(model4_id)

        # Fifth model (optional)
        add_model5 = st.sidebar.checkbox(
            "Add fifth model", value=False, key="add_model5"
        )
        if add_model5:
            model5_display = st.sidebar.selectbox(
                "Model 5",
                display_names,
                key="model_5_select",
                help="Select the fifth model for comparison",
            )

            if model5_display == "Other (custom)":
                model5_custom = st.sidebar.text_input(
                    "Custom Model 5",
                    value="",
                    help="Enter a custom model identifier",
                    key="model_5_custom",
                )
                if model5_custom.strip():
                    selected_models.append(model5_custom.strip())
            else:
                model5_id = model_options[model5_display]
                if model5_id not in selected_models:  # Avoid duplicates
                    selected_models.append(model5_id)

        # Display selected models
        if selected_models:
            st.sidebar.info(f"✅ Selected {len(selected_models)} model(s)")
            for i, model in enumerate(selected_models, 1):
                # Try to find display name for the ID, otherwise use ID
                display_name = next(
                    (k for k, v in model_options.items() if v == model), model
                )
                st.sidebar.caption(f"{i}. {display_name}")

        return selected_models

    def _render_main_content(self):
        """Render main content area."""
        col1, col2 = st.columns([2, 1])

        with col1:
            self.custom_prompt = self._render_prompt_config()

        with col2:
            self._render_status()

        st.markdown("---")

        # Run Evaluation button
        if st.button(
            "Run Evaluation",
            type="primary",
            disabled=not self.selected_task or not self.selected_models,
        ):
            self._run_benchmark()

        # Display results if they exist (even after page reruns)
        if st.session_state.last_results is not None:
            st.markdown("---")
            self._display_success_results(st.session_state.last_results)

    def _render_prompt_config(self) -> Optional[str]:
        """Render prompt configuration section."""
        st.subheader("Prompt Configuration")
        use_custom = st.checkbox("Use Custom Prompt Template")

        if use_custom:
            st.subheader("Custom Prompt Template")
            custom_prompt = st.text_area(
                "Enter your prompt template:",
                height=100,
                help="Use placeholders like {text}, {question}, etc.",
                placeholder="Example: Analyze the sentiment: {text}",
            )
            if custom_prompt:
                st.success("✅ Custom prompt will be used")
            return custom_prompt
        else:
            st.info("Default prompt template will be used")
            return None

    def _render_status(self):
        """Render status panel."""
        st.subheader("Benchmark Status")
        if self.selected_task:
            # st.success("✅ Configuration Ready")
            st.write(f"**Task:** {self.selected_task}")

            if self.selected_models:
                st.write(f"**Models:** {len(self.selected_models)}")
            else:
                st.write("**Models:** None selected")

            st.write(f"**Samples:** {self.number_of_samples}")

            # Dataset status
            if st.session_state.uploaded_dataset:
                st.write(
                    f"**Dataset:** Custom ({st.session_state.uploaded_dataset.name})"
                )
            else:
                # st.write("**Dataset:** Default")
                print("using default dataset")

            if self.use_semantic_matching:
                st.write(
                    f"**Evaluation:** Metrics + LLM as a Judge ({self.selected_gemini_model})"
                )
            else:
                st.write("**Evaluation:** Metrics")

            st.write("💡 API keys are only stored in memory for this session")
        else:
            st.warning("⚠️ Please select a task")

    def _run_benchmark(self):
        """Execute benchmark for multiple models with real-time progress tracking."""
        # Validate API keys
        api_key_to_use = None
        if st.session_state.provider == "openrouter":
            if not self.api_key:
                st.error("❌ Please enter an OpenRouter API key")
                return
            api_key_to_use = self.api_key
        elif st.session_state.provider == "groq":
            if not self.groq_api_key:
                st.error("❌ Please enter a Groq API key")
                return
            api_key_to_use = self.groq_api_key

        if self.use_semantic_matching and not self.gemini_api_key:
            st.error("❌ Please enter a Gemini API key to use semantic matching")
            return

        if not self.selected_models:
            st.error("❌ Please select at least one model")
            return

        # Create containers for progress tracking
        progress_container = st.container()

        with progress_container:
            st.markdown("### 🔄 Benchmark Progress")

            # Progress bar and status
            progress_bar = st.progress(0)
            status_text = st.empty()

            # Detailed progress metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                current_stage = st.empty()
            with col2:
                progress_percent = st.empty()
            with col3:
                samples_info = st.empty()

            # Initialize
            current_stage.metric("Current Stage", "Initializing...")
            progress_percent.metric("Progress", "0%")
            samples_info.metric("Status", "Starting")

            # Define progress callback
            def update_progress(current: int, total: int, status: str):
                """Update progress bar and metrics."""
                progress_value = current / max(total, 1)
                progress_bar.progress(progress_value)
                status_text.info(f"📊 {status}")

                # Determine stage
                if current < 10:
                    stage = "🔧 Initialization"
                elif current < 20:
                    stage = "📂 Data Loading"
                elif current < 80:
                    stage = "⚙️ Processing"
                elif current < 90:
                    stage = "📊 Evaluation"
                elif current < 100:
                    stage = "📝 Report Generation"
                else:
                    stage = "✅ Complete"

                current_stage.metric("Current Stage", stage)
                progress_percent.metric("Progress", f"{current}%")
                samples_info.metric(
                    "Status", status.split(":")[-1].strip() if ":" in status else status
                )

            try:
                # Run Evaluation with multiple models
                results = self.orchestrator.run_multiple(
                    task=BenchmarkTask(self.selected_task),
                    model_names=self.selected_models,
                    api_key=api_key_to_use,
                    provider=st.session_state.provider,
                    custom_prompt=self.custom_prompt,
                    number_of_samples=self.number_of_samples,
                    gemini_api_key=(
                        self.gemini_api_key if self.use_semantic_matching else None
                    ),
                    gemini_model_name=(
                        self.selected_gemini_model
                        if self.use_semantic_matching
                        else None
                    ),
                    use_semantic_matching=self.use_semantic_matching,
                    progress_callback=update_progress,
                    uploaded_dataset=st.session_state.uploaded_dataset,
                    enable_checkpoint_mode=self.enable_checkpoint_mode,
                    checkpoint_interval=self.checkpoint_interval,
                )

                if results["success"]:
                    status_text.success("🎉 Benchmark completed successfully!")
                    # Store results in session state to persist across reruns
                    st.session_state.last_results = results
                    # Trigger a rerun to display results
                    st.rerun()
                else:
                    status_text.error(f"❌ Benchmark failed: {results['error']}")
                    st.session_state.last_results = None

            except Exception as e:
                progress_bar.progress(0.0)
                
                # Extract error type if available
                error_type = "Error"
                error_msg = str(e)
                
                if isinstance(e, RateLimitError):
                    error_type = "Rate Limit Error"
                    error_msg = "Too many requests - API rate limit exceeded"
                elif isinstance(e, PaymentError):
                    error_type = "Payment/Billing Error"
                    error_msg = "Payment or quota issue - check your account balance"
                elif isinstance(e, TokenLimitError):
                    error_type = "Token Limit Error"
                    error_msg = "Request exceeds maximum token limits"
                elif isinstance(e, TimeoutError):
                    error_type = "Timeout Error"
                    error_msg = "Request timed out - check your connection"
                elif isinstance(e, ClientError):
                    error_type = e.error_type.replace("_", " ").title() + " Error"
                    error_msg = str(e)
                
                status_text.error(f"❌ [{error_type}] {error_msg}")
                current_stage.metric("Current Stage", "❌ Failed")
                st.error(f"❌ [{error_type}] {error_msg}")
                st.session_state.last_results = None

    def _display_success_results(self, results: Dict[str, Any]):
        """Display successful benchmark results for multiple models."""
        # Create a unique identifier for this result set
        result_id = f"{results.get('excel_path', '')}_{results.get('detailed_samples_path', '')}"

        # Store file data in session state only once per result set
        if (
            "current_result_id" not in st.session_state
            or st.session_state.current_result_id != result_id
        ):
            st.session_state.current_result_id = result_id

            # Load summary Excel file
            if results.get("excel_path"):
                try:
                    with open(results["excel_path"], "rb") as f:
                        st.session_state.excel_file_data = f.read()
                    st.session_state.excel_filename = Path(results["excel_path"]).name
                except Exception as e:
                    st.session_state.excel_file_data = None
                    st.session_state.excel_filename = None
            else:
                st.session_state.excel_file_data = None
                st.session_state.excel_filename = None

            # Load detailed samples file
            if results.get("detailed_samples_path"):
                try:
                    with open(results["detailed_samples_path"], "rb") as f:
                        st.session_state.detailed_file_data = f.read()
                    st.session_state.detailed_filename = Path(
                        results["detailed_samples_path"]
                    ).name
                except Exception as e:
                    st.session_state.detailed_file_data = None
                    st.session_state.detailed_filename = None
            else:
                st.session_state.detailed_file_data = None
                st.session_state.detailed_filename = None

            # Load comparison Excel file (if multiple models)
            if results.get("comparison_excel_path"):
                try:
                    with open(results["comparison_excel_path"], "rb") as f:
                        st.session_state.comparison_file_data = f.read()
                    st.session_state.comparison_filename = Path(
                        results["comparison_excel_path"]
                    ).name
                except Exception as e:
                    st.session_state.comparison_file_data = None
                    st.session_state.comparison_filename = None
            else:
                st.session_state.comparison_file_data = None
                st.session_state.comparison_filename = None

        # Add download buttons at the top
        st.markdown("### 📥 Download Results")

        # Check if multi-model
        is_multi_model = (
            results.get("model_results") is not None
            and len(results.get("model_results", {})) > 1
        )

        if is_multi_model:
            col1, col2 = st.columns(2)

            with col1:
                if st.session_state.get("comparison_file_data"):
                    st.download_button(
                        label="📈 Download Comparison Summary",
                        data=st.session_state.comparison_file_data,
                        file_name=st.session_state.comparison_filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary",
                        use_container_width=True,
                        help="Side-by-side comparison of all models",
                        key="download_comparison_btn",
                    )
                elif results.get("comparison_excel_path"):
                    st.warning("Could not load comparison file")

            with col2:
                if st.session_state.get("detailed_file_data"):
                    st.download_button(
                        label="📊 Download Detailed Samples (All Models)",
                        data=st.session_state.detailed_file_data,
                        file_name=st.session_state.detailed_filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="secondary",
                        use_container_width=True,
                        help="Includes input data, model outputs, expected results, and judge responses for all models",
                        key="download_detailed_btn",
                    )
                elif results.get("detailed_samples_path"):
                    st.warning("Could not load detailed samples file")
        else:
            # Single model layout
            col1, col2 = st.columns(2)

            with col1:
                if st.session_state.get("excel_file_data"):
                    st.download_button(
                        label="📥 Download Summary Results",
                        data=st.session_state.excel_file_data,
                        file_name=st.session_state.excel_filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary",
                        use_container_width=True,
                        key="download_summary_btn",
                    )
                elif results.get("excel_path"):
                    st.warning("Could not load summary Excel file for download")

            with col2:
                if st.session_state.get("detailed_file_data"):
                    st.download_button(
                        label="📊 Download Detailed Samples",
                        data=st.session_state.detailed_file_data,
                        file_name=st.session_state.detailed_filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="secondary",
                        use_container_width=True,
                        help="Includes input data, model outputs, expected results, and judge responses",
                        key="download_detailed_btn",
                    )
                elif results.get("detailed_samples_path"):
                    st.warning("Could not load detailed samples file")

        st.markdown("---")

        # Rest of the display logic
        stats = results.get("stats", {})
        model_results = results.get("model_results", {})
        semantic_enabled = stats.get("semantic_matching_enabled", False)

        if semantic_enabled:
            tab1, tab2, tab3, tab4 = st.tabs(
                [
                    "📊 Summary",
                    "🧠 LLM Analysis",
                    "📈 Detailed Scores",
                    "📋 Statistics",
                ]
            )

            with tab1:
                self._display_summary(results)

            with tab2:
                self._display_semantic_analysis(results)

            with tab3:
                st.subheader("Detailed Scores")
                if model_results:
                    for model_name, data in model_results.items():
                        with st.expander(f"{model_name}", expanded=True):
                            st.json(data.get("scores", {}))
                else:
                    st.json(results.get("scores", {}))

            with tab4:
                st.subheader("Processing Statistics")
                if model_results:
                    for model_name, data in model_results.items():
                        with st.expander(f"{model_name}", expanded=True):
                            st.json(data.get("stats", {}))
                else:
                    st.json(results.get("stats", {}))
        else:
            tab1, tab2, tab3 = st.tabs(
                ["📊 Summary", "📈 Detailed Scores", "📋 Statistics"]
            )

            with tab1:
                self._display_summary(results)

            with tab2:
                st.subheader("Detailed Scores")
                if model_results:
                    for model_name, data in model_results.items():
                        with st.expander(f"{model_name}", expanded=True):
                            st.json(data.get("scores", {}))
                else:
                    st.json(results.get("scores", {}))

            with tab3:
                st.subheader("Processing Statistics")
                if model_results:
                    for model_name, data in model_results.items():
                        with st.expander(f"{model_name}", expanded=True):
                            st.json(data.get("stats", {}))
                else:
                    st.json(results.get("stats", {}))

    def _display_summary(self, results: Dict[str, Any]):
        """Display results summary for multiple models."""
        st.subheader("Benchmark Summary")
        stats = results.get("stats", {})
        scores = results.get("scores", {})

        # Check if this is a multi-model result
        model_results = results.get("model_results", {})

        if model_results:
            # Create tabs for each model
            tabs = st.tabs([name.replace(":free", "") for name in model_results.keys()])

            for tab, model_name in zip(tabs, model_results.keys()):
                with tab:
                    model_data = model_results[model_name]
                    model_scores = model_data.get("scores", {})
                    model_stats = model_data.get("stats", {})

                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric("Total Examples", model_stats.get("n_examples", 0))

                    with col2:
                        st.metric("API Errors", model_stats.get("n_errors", 0))

                    with col3:
                        n_examples = model_stats.get("n_examples", 1)
                        n_errors = model_stats.get("n_errors", 0)
                        success_rate = (
                            (n_examples - n_errors) / max(n_examples, 1)
                        ) * 100
                        st.metric("API Success Rate", f"{success_rate:.1f}%")

                    with col4:
                        if isinstance(model_scores, dict):
                            # if "accuracy" in model_scores:
                            #     st.metric("Accuracy", f"{model_scores['accuracy']:.3f}")
                            # if "f1" in model_scores:
                            #     st.metric("F1", f"{model_scores['f1']:.3f}")
                            # if "EM" in model_scores:
                            #     st.metric("Exact Match", f"{model_scores['EM']:.3f}")
                            if "ROUGE" in model_scores:
                                st.metric("ROUGE-L", f"{model_scores['ROUGE']:.3f}")

            # Comparison table
            st.write("### Comparison Table")
            comparison_data = []
            for model_name, model_data in model_results.items():
                model_scores = model_data.get("scores", {})
                model_stats = model_data.get("stats", {})

                row = {
                    "Model": model_name.replace(":free", ""),
                    "Total Examples": model_stats.get("n_examples", 0),
                    "Errors": model_stats.get("n_errors", 0),
                }

                # Add main score metric
                if isinstance(model_scores, dict):
                    if "accuracy" in model_scores:
                        row["Accuracy"] = f"{model_scores['accuracy']:.3f}"
                        if "f1" in model_scores:
                            row["F1"] = f"{model_scores['f1']:.3f}"
                        if "EM" in model_scores:
                            row["EM"] = f"{model_scores['EM']:.3f}"
                        if "ROUGE" in model_scores:
                            row["ROUGE-L"] = f"{model_scores['ROUGE']:.3f}"
                    elif "rouge1" in model_scores:
                        row["ROUGE-1"] = f"{model_scores['rouge1']:.3f}"
                    elif "EM" in model_scores:
                        row["EM"] = f"{model_scores['EM']:.3f}"
                        if "ROUGE" in model_scores:
                            row["ROUGE-L"] = f"{model_scores['ROUGE']:.3f}"

                comparison_data.append(row)

            if comparison_data:
                df_comparison = pd.DataFrame(comparison_data)
                st.dataframe(df_comparison)
        else:
            # Single model display (backward compatibility)
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Examples", stats.get("n_examples", 0))

            with col2:
                st.metric("API Request Errors", stats.get("n_errors", 0))

            with col3:
                n_examples = stats.get("n_examples", 1)
                n_errors = stats.get("n_errors", 0)
                success_rate = ((n_examples - n_errors) / max(n_examples, 1)) * 100
                st.metric("API Success Rate", f"{success_rate:.1f}%")

            with col4:
                if isinstance(scores, dict):
                    if "accuracy" in scores:
                        st.metric("Accuracy", f"{scores['accuracy']:.3f}")
                        if "f1" in scores:
                            st.metric("F1", f"{scores['f1']:.3f}")
                        if "EM" in scores:
                            st.metric("Exact Match", f"{scores['EM']:.3f}")
                        if "ROUGE" in scores:
                            st.metric("ROUGE-L", f"{scores['ROUGE']:.3f}")
                    elif "rouge1" in scores:
                        st.metric("ROUGE-1", f"{scores['rouge1']:.3f}")
                    elif "EM" in scores:
                        st.metric("Exact Match", f"{scores['EM']:.3f}")
                        if "ROUGE" in scores:
                            st.metric("ROUGE-L", f"{scores['ROUGE']:.3f}")

    def _display_semantic_analysis(self, results: Dict[str, Any]):
        """Display detailed semantic matching analysis."""
        st.subheader("Semantic Matching Analysis")
        stats = results.get("stats", {})
        model_results = results.get("model_results", {})

        if not stats.get("semantic_matching_enabled", False):
            st.info("Semantic matching was not enabled for this run")
            return

        if model_results:
            # Multi-model display
            tabs = st.tabs([name.replace(":free", "") for name in model_results.keys()])
            for tab, model_name in zip(tabs, model_results.keys()):
                with tab:
                    model_stats = model_results[model_name].get("stats", {})
                    self._render_semantic_metrics(model_stats)
        else:
            # Single model display
            self._render_semantic_metrics(stats)

        with st.expander("ℹ️ What is Semantic Matching?"):
            st.markdown(
                """
            **Semantic Matching** uses Google's Gemini AI to evaluate whether model outputs convey 
            the same meaning as reference answers, even if worded differently.
            
            **Benefits:**
            - Handles paraphrasing and synonyms
            - Considers different writing styles
            - Accounts for Arabic dialectical variations
            - Provides confidence scores for each match
            """
            )

    def _render_semantic_metrics(self, stats: Dict[str, Any]):
        """Render semantic metrics for a single model."""
        st.markdown("### Key Metrics")
        col1, col2, col3 = st.columns(3)

        with col1:
            semantic_matches = stats.get("semantic_matches", 0)
            st.metric("Semantic Matches", semantic_matches)

        with col2:
            semantic_match_rate = stats.get("semantic_match_rate", 0.0) * 100
            st.metric("Semantic Match Rate", f"{semantic_match_rate:.1f}%")

        with col3:
            avg_confidence = stats.get("avg_semantic_confidence", 0.0)
            st.metric("Avg Confidence", f"{avg_confidence:.2f}")

        st.markdown("---")
        st.markdown("### Insights")

        if avg_confidence >= 0.7:
            st.success(
                "✅ High confidence - model outputs are semantically very close to references"
            )
        elif avg_confidence >= 0.4:
            st.warning(
                "⚠️ Moderate confidence - some outputs differ but convey similar meaning"
            )
        else:
            st.error("❌ Low confidence - significant semantic differences")
