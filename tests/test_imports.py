import importlib


def test_src_modules_import():
    modules = [
        "src.data_preprocessing",
        "src.energy_opportunity",
        "src.evaluation",
        "src.feature_engineering",
        "src.figure_generation",
        "src.hybrid_analysis",
        "src.lbnl_pipeline",
        "src.models",
        "src.plotting",
        "src.recommendation_policy",
    ]
    for module in modules:
        importlib.import_module(module)
