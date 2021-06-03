import sys
from os import path

from setuptools import find_packages, setup

try:
    pkg_name = 'executor-normalizer'
    pkg_slug = 'normalizer'
    libinfo_py = path.join(pkg_slug, '__init__.py')
    libinfo_content = open(libinfo_py, 'r', encoding='utf8').readlines()
    version_line = [l.strip() for l in libinfo_content if l.startswith('__version__')][
        0
    ]
    exec(version_line)  # produce __version__
except FileNotFoundError:
    __version__ = '0.0.0'

with open('README.md', 'r') as fh:
    long_description = fh.read()

with open('requirements.txt') as f:
    base_dep = f.read().splitlines()

# remove blank lines and comments
base_dep = [
    x.strip()
    for x in base_dep
    if ((x.strip()[0] != '#') and (len(x.strip()) > 3) and '-e git://' not in x)
]

setup(
    name=pkg_name,
    packages=find_packages(
        exclude=['*.tests', '*.tests.*', 'tests.*', 'tests', 'test', 'docs']
    ),
    version=__version__,
    include_package_data=True,
    author='felix.wang',
    author_email='felix.wang@jina.ai',
    description='Jina executor docker image normalizer',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/jina-ai/executor-normalizer',
    install_requires=base_dep,
    setup_requires=[
        'setuptools>=18.0',
        'pytest-runner',
        'black==20.8b1',
        'isort==4.3.21',
    ],
    tests_require=['pytest'],
    python_requires='>=3.6',
    entry_points={'console_scripts': ['normalizer=normalizer.main:cli']},
    classifiers=[
        'Programming Language :: Python :: 3',
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: Apache Software License',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
    ],
)
