import os
from setuptools import setup, find_packages

from channels_irc import __version__

readme = os.path.join(os.path.dirname(__file__), 'README.md')

setup(
    name='channels_irc',
    version=__version__,
    url='https://github.com/AdvocatesInc/channels-chatbot',
    author='Advocates, Inc',
    author_email='admin@adv.gg',
    description='Interface server connecting Django\'s channels and IRC',
    long_description=open(readme).read(),
    license='Proprietary and confidential',
    zip_safe=False,
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'irc>=16.1',
        'asgiref>=2.1.6',
        'channels==2.0.2',
    ],
    entry_points={'console_scripts': [
        'channels-irc = channels_irc.cli:CLI.entrypoint'
    ]},
)
