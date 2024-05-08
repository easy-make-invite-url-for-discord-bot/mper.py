from setuptools import setup, find_packages

setup(
    name='mper',
    version='0.1',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'mper=mper.mper:main',
        ],
    },
    install_requires=[
        
    ],
    python_requires='>=3.6',
    author='FreeWiFiTech',
    author_email='wifi@freewifitech.jp',
    description='A tool to generate Discord bot invite links based on code analysis.'
)