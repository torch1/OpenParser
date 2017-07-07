from setuptools import setup, find_packages
from openparser import __version__

setup(
    name='OpenParser',
    version=__version__,
    description='Parse webpages and extract the most important information.',
    url='https://github.com/torch1/openparser',
    author='Miles McCain',
    author_email='miles@rmrm.io',
    license='MIT',
    packages=find_packages(),
    install_requires=[
        'lxml>=3.3.5',
        'beautifulsoup4>=4.6.0',
        'bs4>=0.0.1',
        'python-dateutil>=1.5',
        'requests>=2.18.1'
    ],
    entry_points={
        'console_scripts': ['openparser = openparser.cli:main']},
    zip_safe=False
)
