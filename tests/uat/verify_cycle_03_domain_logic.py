import marimo

__generated_with = "0.10.14"
app = marimo.App(width="medium")


@app.cell
def _() -> tuple[()]:

    from src.domain_models.config import DispatcherConfig
    from src.domain_models.manifest import CycleManifest
    from src.services.async_dispatcher import AsyncDispatcher

    # 1. Initialize Dispatcher with settings
    config = DispatcherConfig(max_concurrent_tasks=4)
    dispatcher = AsyncDispatcher(config)

    # 2. Simulate Cycle Manifests (Some with dependencies)
    manifests = [
        CycleManifest(id="01", status="completed"),
        CycleManifest(id="02", depends_on=["01"]),
        CycleManifest(id="03", depends_on=["01"]),
        CycleManifest(id="04", depends_on=["02", "03"]),
        CycleManifest(id="05"),  # Independent
    ]

    # 3. Resolve DAG
    batches = dispatcher.resolve_dag(manifests)

    # Expected output:
    # Batch 1: 02, 03, 05 (Since 01 is completed, 02 and 03 are ready. 05 is independent)
    # Batch 2: 04
    print("Resolved Execution Batches:")  # noqa: T201
    for i, batch in enumerate(batches, 1):
        ids = [c.id for c in batch]
        print(f"Batch {i}: {ids}")  # noqa: T201

    assert len(batches) == 2, "Should resolve into 2 batches"
    assert len(batches[0]) == 3, "Batch 1 should have 3 tasks"
    assert len(batches[1]) == 1, "Batch 2 should have 1 task"
    print("DAG Resolution logic is correct.")  # noqa: T201

    return ()


if __name__ == "__main__":
    app.run()
