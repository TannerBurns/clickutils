import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

setup(
    name='click_dynamics',
    version='0.0.2',
    packages=find_packages(exclude=['examples']),
    include_package_data=True,
    description='Utilities for dynamically adding commands to click cli',
    long_description=README,
    url='https://www.github.com/tannerburns/click_dynamics',
    author='Tanner Burns',
    author_email='tjburns102@gmail.com',
    install_requires=[
        'click',
    ],
    classifiers=[
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.7',
    ],
)
