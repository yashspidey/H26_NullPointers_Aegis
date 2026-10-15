"""
Streamlit wrapper for RepoRescue-AI — calls the CLI and displays results.
This is a thin UI wrapper; the core logic remains in `re-rescue` CLI.
"""

import streamlit as st
import subprocess
import tempfile
import os
from pathlib import Path

st.set_page_config(page_title="RepoRescue-AI", page_icon="🔍", layout="wide")

st.title("🔍 RepoRescue-AI: Repository Maintenance Analyzer")
st.caption("AI-powered Dependency Exit Capsule generator — [GitHub](https://github.com/YOUR_USERNAME/RepoRescue-AI)")

with st.sidebar:
    st.header("Settings")
    repo_input = st.text_input("Repository Path or URL", placeholder="C:\\path\\to\\repo or https://github.com/user/repo")
    use_ai = st.checkbox("Enable AI Analysis (requires Hermes + local model)", value=False)
    run_btn = st.button("Analyze", type="primary", disabled=not repo_input)

    st.divider()
    st.markdown("""
    **How it works:**
    1. Enter a local path or Git URL
    2. Click Analyze
    3. View Dependency Exit Capsule
    
    **Core CLI:** `re-rescue analyze <path> [--no-ai]`
    """)

if run_btn:
    with st.spinner("Analyzing repository..."):
        # Handle local path vs URL
        if repo_input.startswith(("http://", "https://", "git@")):
            # Clone to temp dir
            with tempfile.TemporaryDirectory() as tmpdir:
                clone_result = subprocess.run(
                    ["git", "clone", "--depth", "1", repo_input, "repo"],
                    cwd=tmpdir, capture_output=True, text=True
                )
                if clone_result.returncode != 0:
                    st.error(f"Clone failed:\n{clone_result.stderr}")
                    st.stop()
                target_path = os.path.join(tmpdir, "repo")
        else:
            target_path = repo_input
            if not os.path.exists(target_path):
                st.error(f"Path not found: {target_path}")
                st.stop()

        # Run re-rescue CLI
        cmd = ["re-rescue", "analyze", target_path]
        if not use_ai:
            cmd.append("--no-ai")
        
        # Add output to temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            output_path = f.name
        
        cmd.extend(["--output", output_path])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            st.error(f"Analysis failed:\n{result.stderr}")
            st.code(result.stdout)
            st.stop()

        # Read and display capsule
        capsule_content = Path(output_path).read_text(encoding="utf-8")
        os.unlink(output_path)

    st.success("Analysis complete!")
    
    # Display capsule
    tab1, tab2, tab3 = st.tabs(["📄 Capsule (Rendered)", "📝 Capsule (Markdown)", "🔧 Raw Output"])
    
    with tab1:
        st.markdown(capsule_content, unsafe_allow_html=True)
    
    with tab2:
        st.code(capsule_content, language="markdown")
    
    with tab3:
        st.code(result.stdout)
        if result.stderr:
            st.code(result.stderr, language="bash")

    # Download button
    st.download_button(
        "📥 Download Capsule",
        capsule_content,
        file_name=f"Dependency_Exit_Capsule_{Path(target_path).name}.md",
        mime="text/markdown"
    )

st.divider()
st.markdown("""
**RepoRescue-AI** — Hackathon 2026 submission  
• CLI-first • Evidence-based • AI-transparent • Local models only  
[View Source](https://github.com/YOUR_USERNAME/RepoRescue-AI) | [Hermes Skill](https://github.com/YOUR_USERNAME/RepoRescue-AI/tree/main/skills/repo-maintenance)
""")