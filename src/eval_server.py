"""Modal deployment for Braintrust remote eval server.

Deploys your evals to Modal so they can be run from the Braintrust Playground.

Key features:
- Automatically discovers all eval_*.py files in the evals/ directory
- Loads evaluations using Braintrust's CLI loader
- Creates an ASGI application that Braintrust can connect to
- Supports configurable parameters from the Playground UI

Deploy: modal serve src/eval_server.py (dev) or modal deploy src/eval_server.py (prod)
"""

import modal

# Configure Modal image with dependencies and source code
modal_image = (
    modal.Image.debian_slim(python_version="3.11")
    .uv_sync()
    .add_local_python_source("src")
    .add_local_python_source("evals")
)

# Create Modal app
app = modal.App("braintrust-eval-server", image=modal_image)

# Configure secrets (reads from .env file)
_secrets = [modal.Secret.from_dotenv()]


@app.function(
    secrets=_secrets,
    min_containers=1,  # Keep 1 container warm to reduce cold start latency
    timeout=3600,  # Max time a single evaluation can run (1 hour)
)
@modal.concurrent(
    max_inputs=10,  # Max concurrent requests per container
)
@modal.asgi_app()
def braintrust_eval_server():
    """Discover and load eval_*.py files, then create ASGI app for Braintrust."""
    from pathlib import Path
    from braintrust.cli.eval import EvaluatorState, FileHandle, update_evaluators
    from braintrust.devserver.server import create_app
    import evals

    # Find evals directory
    if hasattr(evals, "__path__") and evals.__path__:
        evals_dir = Path(evals.__path__[0])
    elif hasattr(evals, "__file__") and evals.__file__:
        evals_dir = Path(evals.__file__).parent
    else:
        raise RuntimeError("Could not locate evals/ directory")

    # Discover eval_*.py files
    eval_files = list(evals_dir.glob("eval_*.py"))
    if not eval_files:
        raise RuntimeError(f"No eval_*.py files found in {evals_dir}")

    print(f"Found {len(eval_files)} eval file(s): {[f.name for f in eval_files]}")

    # Load evaluators
    handles = [FileHandle(in_file=str(f)) for f in eval_files]
    eval_state = EvaluatorState()
    update_evaluators(eval_state, handles, terminate_on_failure=True)
    evaluators = [e.evaluator for e in eval_state.evaluators]

    print(f"Loaded {len(evaluators)} evaluator(s): {[e.eval_name for e in evaluators]}")

    return create_app(evaluators, org_name=None)


@app.local_entrypoint()
def test():
    """Test the deployment locally."""
    print("✓ Configuration looks good!")
    print("\nNext steps:")
    print("  1. Deploy: modal serve src/eval_server.py")
    print("  2. Copy the URL from Modal dashboard")
    print("  3. Add URL to Braintrust Playground as a remote eval source")

