from setuptools import setup

setup(
    name="seppo",
    version="20051211",
    license="BSD",
    author="Andrew Straw",
    author_email="strawman@astraw.com",
    url="http://www.its.caltech.edu/~astraw/seppo.html",
    
    package_dir = {'seppo' : 'lib/seppo'},
    packages = ['seppo'],

    entry_points = {'console_scripts': [
    'seppo_serv_process = seppo:start_seppo_enslaved_server',
    ],
                    },
    
    )
