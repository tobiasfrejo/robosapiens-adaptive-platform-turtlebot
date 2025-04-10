from setuptools import setup, find_packages

setup(
    name="dyn-lola",
    version="0.1.0",
    description="Allows for generation of LOLA specifications including for dynamic properties.",
    python_requires=">=3.10",
    packages=find_packages(include=["dyn_lola", "src.*"]),
    install_requires = [
        line.strip() for line in open('requirements.txt')],
)