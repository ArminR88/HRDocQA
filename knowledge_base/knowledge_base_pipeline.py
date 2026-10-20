import sys
from pathlib import Path

_this_file = Path(__file__).resolve()
_package_parent = _this_file.parents[1]
if str(_package_parent) not in sys.path:
    sys.path.insert(0, str(_package_parent))

import logging
import time

from knowledge_base.helpers.shared_helper import format_elapsed_seconds, setup_logging
from knowledge_base.stages.assembling_stage import run_stage as run_assembling_stage
from knowledge_base.stages.chunking_stage import run_stage as run_chunking_stage
from knowledge_base.stages.embedding_stage import run_stage as run_embedding_stage
from knowledge_base.stages.monitoring_stage import run_stage as run_monitoring_stage


def run_pipeline(
    verbose=False,
    cond_run_chunking_stage=True,
    cond_run_embedding_stage=True,
    cond_run_assembling_stage=True,
    cond_run_monitoring_stage=True,
):
    """
    Run the complete knowledge-base pipeline in stage order.

    Arguments:
        verbose (bool): If True, enable verbose logging.
        cond_run_chunking_stage (bool): Whether to execute stage 1.
        cond_run_embedding_stage (bool): Whether to execute stage 2.
        cond_run_assembling_stage (bool): Whether to execute stage 3.
        cond_run_monitoring_stage (bool): Whether to execute stage 4.

    Returns:
        None

    Example:
        >>> run_pipeline(verbose=True)
    """
    setup_logging(verbose=verbose)
    pipeline_start = time.time()

    if cond_run_chunking_stage == True:
        run_chunking_stage()
    if cond_run_embedding_stage == True:
        run_embedding_stage()
    if cond_run_assembling_stage == True:
        run_assembling_stage()
    if cond_run_monitoring_stage == True:
        run_monitoring_stage()

    elapsed = time.time() - pipeline_start
    formatted_elapsed = format_elapsed_seconds(elapsed)
    logging.info("Total pipeline runtime: %s", formatted_elapsed)


if __name__ == "__main__":
    run_pipeline()
    print("Pipeline finished.")
