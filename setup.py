from setuptools import setup, find_packages

setup(
    name='oesdk',
    packages=find_packages(),
    install_requires=[
        'pandas==1.2.3',
        'requests==2.25.1',
        'wheel',
    ],
    python_requires='==3.9.*',
)
