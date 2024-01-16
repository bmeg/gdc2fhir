from setuptools import setup, find_packages

__version__ = '0.0.0'

setup(
    name='gdc2fhir',
    version=__version__,
    description="Mapping GDC's schema to Ellrot's lab FHIR schema.",
    long_description=open('README.md').read(),
    # url='',
    author='https://ellrottlab.org/',  
    packages=find_packages(),
    """
    entry_points={
        'console_scripts': []
    },
    install_requires=[
        x,
        y,
        z,
    ],
    """
    tests_require=['pytest'],
    classifiers=[
        # 'Development Status :: 3 - Alpha',
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