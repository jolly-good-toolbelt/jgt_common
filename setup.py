import os
import setuptools

NAME = 'qecommon_tools'
DESCRIPTION = 'Collection of miscellaneous helper methods'
VERSION = None

CONSOLE_SCRIPTS = [
    'uuid-replacer=qecommon_tools.uuid_replacer:main',
]

INSTALL_REQUIRES = [
    'requests>=2.10',
    'wrapt',
]

TESTS_REQUIRE = [
    'pytest'
]

EXTRAS_REQUIRE = {}

here = os.path.abspath(os.path.dirname(__file__))

about = {}
if not VERSION:
    with open(os.path.join(here, NAME, '__version__.py')) as f:
        exec(f.read(), about)
else:
    about['__version__'] = VERSION


setuptools.setup(name=NAME,
                 version=about['__version__'],
                 description=DESCRIPTION,
                 url='https://github.rackspace.com/QualityEngineering/QE-Tools',
                 author='Rackspace QE',
                 author_email='qe-tools-contributors@rackspace.com',
                 license='MIT',
                 entry_points={
                     'console_scripts': CONSOLE_SCRIPTS,
                 },
                 install_requires=INSTALL_REQUIRES,
                 packages=setuptools.find_packages(),
                 tests_require=TESTS_REQUIRE,
                 include_package_data=True,
                 zip_safe=False,
                 extras_require=EXTRAS_REQUIRE,
                 )
