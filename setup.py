import os
from setuptools import setup, find_packages

from channels_chatbot import __version__

readme = os.path.join(os.path.dirname(__file__), 'README.md')

setup(
    name='channels_chatbot',
    version=__version__,
    url='https://github.com/AdvocatesInc/channels-chatbot',
    author='Advocates, Inc',
    author_email='admin@adv.gg',
    description='Interface server connecting django-channels and IRC',
    long_description=open(readme).read(),
    license='Proprietary and confidential',
    zip_safe=False,
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'asgiref~=1.1',
        'irc>=16.1',
        'channels>=1.1.6',
    ],
    entry_points={'console_scripts': [
        'channels-chatbot = channels_chatbot.cli:CLI.entrypoint'
    ]},
)
