from setuptools import setup, find_packages

setup(
    name='SchemPy',
    use_scm_version=True,
    packages=find_packages(),
    setup_requires=['setuptools_scm'],
    install_requires=[
        'nbtlib',
        'numpy'
    ],
    extras_require={
        'test': ['deepdiff'],
    },
    author='Patrizio Spagnardi III',
    author_email='mmmfrieddough@gmail.com',
    description='Python module for working with Minecraft schematics.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/mmmfrieddough/SchemPy',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        # Add other Python versions you support here
    ],
    python_requires='>=3.6',  # Specify the minimum Python version required
)
