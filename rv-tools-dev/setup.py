from setuptools import setup, find_packages

setup(
    name="rv-tools",
    version="0.1.0",
    description="Tools to help runtime verification implementation",
    python_requires=">=3.10",
    packages=find_packages(include=["rv_tools", "rv_tools.*"]),
    install_requires = [
        line.strip() for line in open('requirements.txt')],
)