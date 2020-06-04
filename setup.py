#!/usr/bin/env python

def main():
    from setuptools import setup

    with open("README.rst", "rt") as inf:
        readme = inf.read()

    version_dict = {}
    init_filename = "boxtree/version.py"
    exec(compile(open(init_filename, "r").read(), init_filename, "exec"),
            version_dict)

    setup(
            name="genpy",
            version=version_dict["VERSION_TEXT"],
            description="AST-based generation of Python source code",
            long_description=readme,
            classifiers=[
                'Development Status :: 4 - Beta',
                'Intended Audience :: Developers',
                'Intended Audience :: Other Audience',
                'Intended Audience :: Science/Research',
                'License :: OSI Approved :: MIT License',
                'Natural Language :: English',
                'Programming Language :: Python',
                'Topic :: Scientific/Engineering',
                'Topic :: Software Development :: Libraries',
                'Topic :: Utilities',
                ],

            author="Andreas Kloeckner",
            author_email="inform@tiker.net",
            license="MIT",
            url="http://documen.tician.de/genpy/",

            packages=["genpy"],
            install_requires=[
                "pytools>=2015.1.2",
                "numpy>=1.6",
                ])
