from setuptools import find_packages, setup

setup(
    name="oesdk",
    packages=find_packages(),
    install_requires=[
        "pandas==1.3.2",
        "requests==2.25.1",
        "wheel",
    ],
    python_requires="==3.8.*",
)
