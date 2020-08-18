from setuptools import setup, find_packages

setup(
    name='oesdk',
    packages=find_packages(),
    install_requires=[
        'pandas==1.1.0',
        'requests==2.22.0',
        'wheel',
    ],
    python_requires='==3.6.*',
)
