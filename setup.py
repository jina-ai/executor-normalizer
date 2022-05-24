from setuptools import find_packages, setup

pkg_name = 'executor-normalizer'
pkg_slug = 'normalizer'

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
    version='0.0.0',
    include_package_data=True,
    package_data={'normalizer': ['resources/*', 'resources/**/*']},
    author='felix.wang',
    author_email='felix.wang@jina.ai',
    description='Jina executor docker image normalizer',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/jina-ai/executor-normalizer',
    install_requires=base_dep,
    setup_requires=[
        'setuptools>=18.0',
    ],
    extras_require={
        'test': [
            'pytest',
            'pytest-timeout',
            'pytest-mock',
            'pytest-cov',
            'pytest-repeat',
            'pytest-reraise',
            'mock',
            'pytest-custom_exit_code',
            'black==22.3.0',
            'jina',
            'flake8',
            'isort',
        ],
    },
    python_requires='>=3.6',
    entry_points={
        'console_scripts': [
            'executor_manager=executor_manager.main:cli',
        ]
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: Apache Software License',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
    ],
)
