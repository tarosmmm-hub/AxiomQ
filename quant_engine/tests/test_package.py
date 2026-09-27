import quant_engine


def test_engine_version_is_exposed() -> None:
    # The engine version is recorded in every experiment for reproducibility.
    assert quant_engine.ENGINE_VERSION == quant_engine.__version__
    assert quant_engine.ENGINE_VERSION.count(".") == 2
