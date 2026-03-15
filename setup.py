from setuptools import find_packages, setup


setup(
    name="codex-token-count",
    version="0.1.0",
    description="CLI for analyzing local Codex token usage",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.11",
    install_requires=["rich>=13.7"],
    entry_points={
        "console_scripts": [
            "codex-token=codex_token_count.cli:main",
        ]
    },
)
