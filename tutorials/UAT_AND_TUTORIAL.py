import marimo

__generated_with = "0.1.0"
app = marimo.App()

@app.cell
def app_cell() -> tuple: # type: ignore
    import os
    import sys

    import pytest

    from src.domain_models.execution import ConflictRegistryItem
    from src.state import CycleState, IntegrationState
    sys.stdout.write("Welcome to Nitpickers 5-Phase Architecture Tutorial.\n")

    state = IntegrationState()
    sys.stdout.write(f"IntegrationState initialized with {len(state.unresolved_conflicts)} conflicts.\n")
    return os, pytest, CycleState, IntegrationState, ConflictRegistryItem

if __name__ == "__main__":
    app.run()
