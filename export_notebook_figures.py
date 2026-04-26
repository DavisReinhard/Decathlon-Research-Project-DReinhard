from __future__ import annotations

import argparse
import base64
from pathlib import Path

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
from jupyter_client.kernelspec import KernelSpecManager


NOTEBOOK_NAME = "Decathlon Project DReinhard.ipynb"
OUTPUT_DIR = Path("artifacts/figures")

TITLE_TO_FILENAME = {
    "Figure 1: (RQ1) Event rank alignment with overall placing": "figure1_rq1_rank_alignment.png",
    "Figure 2: (RQ2) Event z-score alignment with overall placing": "figure2_rq2_z_alignment.png",
    "Figure 3: (RQ3) Conference-to-conference variability by event (rank method)": "figure3_conf_variability_rank.png",
    "Figure 4: (RQ3) Conference-to-conference variability by event (z-score method)": "figure4_conf_variability_z.png",
    "Figure 5: Event importance by conference (z-score method)": "figure5_conf_event_heatmap_z.png",
    "Figure 6: Meet-to-meet variability of event importance (z-score method)": "figure6_meet_variability_boxplot_z.png",
    "RQ1: Event strength vs stability (rank method)": "rq1_strength_vs_stability.png",
}


def resolve_kernel_name(notebook: nbformat.NotebookNode) -> str:
    requested = (
        notebook.metadata.get("kernelspec", {}).get("name")
        if notebook.metadata.get("kernelspec")
        else None
    )
    manager = KernelSpecManager()
    installed = manager.find_kernel_specs()

    candidates = [requested, "python3", "python"]
    for candidate in candidates:
        if candidate and candidate in installed:
            return candidate

    if installed:
        return sorted(installed.keys())[0]

    raise RuntimeError(
        "No Jupyter kernel is installed. Install one with: "
        "`python -m pip install ipykernel && python -m ipykernel install --user --name python3`"
    )


def execute_notebook(notebook_path: Path, timeout_seconds: int) -> nbformat.NotebookNode:
    with notebook_path.open("r", encoding="utf-8") as f:
        notebook = nbformat.read(f, as_version=4)

    kernel_name = resolve_kernel_name(notebook)
    executor = ExecutePreprocessor(timeout=timeout_seconds, kernel_name=kernel_name)
    executor.preprocess(notebook, {"metadata": {"path": str(notebook_path.parent)}})
    return notebook


def extract_images(executed_nb: nbformat.NotebookNode, output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    found: dict[str, Path] = {}

    for cell in executed_nb.cells:
        if cell.cell_type != "code":
            continue

        source = cell.source or ""
        title = next((t for t in TITLE_TO_FILENAME if t in source), None)
        if title is None or title in found:
            continue

        outputs = cell.get("outputs", [])
        png_b64 = None
        for out in outputs:
            if out.get("output_type") not in {"display_data", "execute_result"}:
                continue
            data = out.get("data", {})
            if "image/png" in data:
                png_b64 = data["image/png"]
                break

        if png_b64 is None:
            continue

        filename = TITLE_TO_FILENAME[title]
        destination = output_dir / filename
        destination.write_bytes(base64.b64decode(png_b64))
        found[title] = destination

    missing = [title for title in TITLE_TO_FILENAME if title not in found]
    if missing:
        missing_text = "\n".join(f"- {m}" for m in missing)
        raise RuntimeError(f"Could not extract all required figures.\nMissing:\n{missing_text}")

    return [found[title] for title in TITLE_TO_FILENAME]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Execute notebook and export key figure PNGs for Streamlit."
    )
    parser.add_argument(
        "--notebook",
        default=NOTEBOOK_NAME,
        help=f"Notebook to execute (default: {NOTEBOOK_NAME})",
    )
    parser.add_argument(
        "--output-dir",
        default=str(OUTPUT_DIR),
        help=f"Output directory for PNGs (default: {OUTPUT_DIR.as_posix()})",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=1800,
        help="Per-cell execution timeout in seconds (default: 1800)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    notebook_path = Path(args.notebook).resolve()
    output_dir = Path(args.output_dir).resolve()

    if not notebook_path.exists():
        raise FileNotFoundError(f"Notebook not found: {notebook_path}")

    executed_nb = execute_notebook(notebook_path, timeout_seconds=args.timeout_seconds)
    exported = extract_images(executed_nb, output_dir)

    print("Exported notebook figures:")
    for path in exported:
        print(f"- {path}")


if __name__ == "__main__":
    main()
