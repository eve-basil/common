from setuptools import setup, find_packages

setup(
    name="basil-common",
    version="0.1.0.dev",
    packages=find_packages(),

    description="Junk drawer of commonly needed functionality for Eve Basil.",
    install_requires=["falcon==0.3.0", "redis==2.10.5", "SQLAlchemy==1.0.10"],
)
