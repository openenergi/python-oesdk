from setuptools import find_packages, setup

setup(
    name="oesdk",
    packages=find_packages(),
    install_requires=[
        "pandas==2.2.*",
        "requests==2.31.*",
        "wheel",
    ],
)
