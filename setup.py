import io

from setuptools import find_packages, setup

with io.open('README.md', 'rt', encoding='utf8') as f:
    readme = f.read()

setup(
    name='lunchbot',
    version='0.5.0',
    url='http://github.com/slyboots/lunchbot',
    license='MIT',
    maintainer='slyboots',
    maintainer_email='me@dakotalorance.com',
    description='simple slackbot for helping us keep track of our lunches at RG',
    long_description=readme,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'flask',
        'slackclient'
    ],
    extras_require={
        'test': [
            'pytest',
            'coverage',
        ],
    },
)
