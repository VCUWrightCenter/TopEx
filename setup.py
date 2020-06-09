from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.readlines()

setup(
    name='medtop',
    version='0.0.7',
    packages=find_packages(),
    url='https://amyolex.github.io/medtop/',
    author='alolex',
    description='',
    install_requires=requirements
)