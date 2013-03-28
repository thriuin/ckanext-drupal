from setuptools import setup, find_packages
import sys, os

version = '0.1.0'

setup(
    name='ckanext-drupal',
    version=version,
    description="CKAN extension for linking packages to nodes in Drupal",
    long_description="""
    """,
    classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='',
    author='Government of Canada',
    author_email='ross.thompson@statcan.gc.ca',
    url='',
    license='MIT',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['ckanext', 'ckanext.drupal'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        # -*- Extra requirements: -*-
    ],
    entry_points=\
    """
    [paste.paster_command]
    drupal=ckanext.drupal.commands:DrupalCommand
    """,
)
