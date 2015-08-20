#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read().replace('.. :changelog:', '')

requirements = [
]

test_requirements = [
    'nose',
    'coverage',
]

setup(
    name='loganalysis',
    version='0.1.0',
    description="A collection of log analysis functions and CLIs",
    long_description=readme + '\n\n' + history,
    author="Alan Kang",
    author_email='alankang@boxnwhis.kr',
    url='https://github.com/box-and-whisker/loganalysis',
    packages=[
        'loganalysis',
    ],
    package_dir={'loganalysis':
                 'loganalysis'},
    include_package_data=True,
    setup_requires=['nose>=1.0'],
    install_requires=requirements,
    license="BSD",
    zip_safe=False,
    keywords='log analysis streaming',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Internet :: Log Analysis',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Logging',
        'Topic :: System :: Networking :: Monitoring',
        'Topic :: System :: Systems Administration',
        'Topic :: Text Processing :: Filters',
    ],
    test_suite='nose.collector',
    tests_require=test_requirements,
)
