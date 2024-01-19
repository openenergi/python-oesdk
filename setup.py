from setuptools import find_packages, setup

setup(
    name="oesdk",
    packages=find_packages(),
    install_requires=[
        "pandas==1.5.3",
        "requests==2.31.0",
        "wheel",
    ],
)
