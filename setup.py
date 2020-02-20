import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

setup(
    name='clickutils',
    version='0.0.5',
    packages=find_packages(exclude=['examples']),
    include_package_data=True,
    description='Extra utils for click library',
    url='https://www.github.com/tannerburns/clickutils',
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
