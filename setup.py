"""
兼容旧版pip的setup.py
推荐使用 pyproject.toml 进行安装
"""
from setuptools import setup, find_packages

setup(
    name="auauth",
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.8",
)
