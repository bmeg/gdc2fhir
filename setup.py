from setuptools import setup, find_packages

__version__ = '0.0.0'

setup(
    name='gdc2fhir',
    version=__version__,
    description="Mapping GDC's schema to Ellrot's lab FHIR schema.",
    long_description=open('README.md').read(),
    url='https://github.com/bmeg/gdc2fhir',
    author='https://ellrottlab.org/',
    packages=find_packages(),
    entry_points={
        'console_scripts': ['gdc2fhir = gdc2fhir.cli:cli']
    },
    install_requires=[
        'charset_normalizer',
        'idna',
        'certifi',
        'requests',
        'pydantic',
        'pytest',
        'click',
        'pathlib',
        'beautifulsoup4',
        'fhir.resources>=7.1.0'  # FHIR® (Release R5, version 5.0.0)
    ],
    tests_require=['pytest'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.9',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Bio-Informatics'
    ],
    platforms=['any'],
    python_requires='>=3.9, <4.0',
)