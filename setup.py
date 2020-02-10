from setuptools import setup, find_packages

setup(
    name='oesdk',
    packages=find_packages(),
    install_requires=[
        'pandas==0.25.3',
        'requests==2.22.0',
        'wheel',
    ],
    python_requires='==3.6',
)
