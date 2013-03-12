from setuptools import setup, find_packages

VERSION = (1, 0, 0, 'dev')

setup(
    name = "biwinning",
    version = ".".join(map(str, VERSION)),
    license = 'BSD',
    description = "",
    author = '',
    packages = find_packages('.'),
    package_dir = {'': 'src'},
    include_package_data = True,
    zip_safe = False,
    setup_requires = ['setuptools_git'],
    install_requires = ['setuptools',
                        'Flask==0.9',
                        'flask-peewee==0.6.3',
                        'python-dateutil==2.1',
                        'simplejson==3.0.7',
    ],
)