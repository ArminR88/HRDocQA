from datetime import date
from pathlib import Path


def _build_run_root(root_name: str = "output_knowledge_base") -> Path:
    """
    Description: Build the dated root directory for a pipeline run.

    Arguments:
        root_name (str): Root output folder name.

    Returns:
        Path: Created dated run-root directory.

    Example:
        >>> _build_run_root()
        PosixPath('output_knowledge_base/2026-10-25')
    """
    # Resolve the module path and project root.
    module_path = Path(__file__)
    resolved_path = module_path.resolve()
    project_root = resolved_path.parents[2]

    # Compute the dated folder name.
    today = date.today()
    dated_folder = today.isoformat()

    # Construct the run-root path.
    run_root = project_root / root_name / dated_folder

    # Create the run-root directory.
    run_root.mkdir(parents=True, exist_ok=True)
    return run_root


def build_output_directories(root_name: str = "output_knowledge_base") -> dict:
    """
    Description: Build output directories for a dated knowledge-base pipeline run.

    Arguments:
        root_name (str): Root output folder name.

    Returns:
        dict: Directory paths with keys:
            - run_root
            - pipeline_summary
            - monitoring
            - banners

    Example:
        >>> dirs = build_output_directories()
        >>> dirs["run_root"].name
        '2026-10-25'
    """
    # Resolve the dated run root.
    run_root = _build_run_root(root_name=root_name)

    # Compose the pipeline sub-directory paths.
    pipeline_summary = run_root / "pipeline_summary"
    monitoring = run_root / "monitoring"
    banners = monitoring / "banners"

    # Create the output directories.
    pipeline_summary.mkdir(parents=True, exist_ok=True)
    monitoring.mkdir(parents=True, exist_ok=True)
    banners.mkdir(parents=True, exist_ok=True)

    # Build the directory mapping.
    directories = {}
    directories["run_root"] = run_root
    directories["pipeline_summary"] = pipeline_summary
    directories["monitoring"] = monitoring
    directories["banners"] = banners
    return directories
