from setuptools import setup, find_packages

setup(
    name='automato',
    author="Jonas Gunz",
    author_mail="himself@jonasgunz.de",
    description="automato",
    version='0.0.0',
    packages=find_packages(),
    entry_points = {
        'console_scripts': ['automato=automato.command_line:main'],
    },
    # TODO Check them
    install_requires=[
        "paramiko",
        "pyparsing",
        "PyYAML",
    ],
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
