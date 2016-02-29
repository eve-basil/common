from setuptools import setup, find_packages

setup(
    name="basil-common",
    version="0.1.0.dev",
    packages=find_packages(),

    description="Junk drawer of commonly needed functionality for Eve Basil.",
    install_requires=["SQLAlchemy==1.0.10", "falcon==0.3.0"],
)
