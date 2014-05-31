"""This module does the (heavy?) work of actually checking out modules with git
and building them.
"""
import glob
import logging
import os
import re
import shutil
import subprocess
import tempfile

import git
import semantic_version

from mypi import settings


def build(repo, branch):
    """Clone the repo, checkout the given branch, and build the package.
    If all is successful, then the resultant package file is put into the
    PACKAGES_DIR
    """
    working_dir = tempfile.mkdtemp()

    try:
        package_filename = raw_build(repo, branch, working_dir)
        shutil.move(package_filename, settings.PACKAGES_DIR)
    finally:
        # Make sure we clean up!
        shutil.rmtree(working_dir)


def raw_build(repo, branch, working_dir):
    """Does the actual work of build.
    It requires a working directory to be specified.
    (It will not delete the directory after it is done.)
    It returns the absolute filename of the resultant package.
    """
    git.Repo.clone_from(repo, working_dir, branch=branch)

    old_cwd = os.getcwd()

    try:
        # Run the package build
        os.chdir(working_dir)
        subprocess.call(["python", "setup.py", "sdist"])

        package_filename = glob.glob("dist/*.tar.gz")[0]
        return os.path.join(working_dir, package_filename)

    finally:
        os.chdir(old_cwd)


def get_all_packages(packages_dir=None):
    """Looks at all the package files in the packages dir and returns a list.
    Each item in the list is a tuple:
    (package_name, sorted_list_of_versions)
    e.g.
    [
        ("mypi", ["1.0.0", "0.9.9"]),
    ]
    """
    if packages_dir is None:
        packages_dir = settings.PACKAGES_DIR

    package_versions = {}

    pattern = os.path.join(packages_dir, "*.tar.gz")
    for raw_filename in glob.glob(pattern):
        filename = os.path.basename(raw_filename)
        components = filename.split("-")
        if len(components) < 2:
            # How odd, the filename isn't of the form name-version.tar.gz
            continue

        # Just to be safe, try to deal with names that have '-'.
        # So the version is the last part, everything before is the name.
        version_string = components[-1].replace(".tar.gz", "")
        version = get_version(version_string)
        name = "-".join(components[:-1])

        if name not in package_versions:
            package_versions[name] = []

        package_versions[name].append(version)

    # Convert the dict into a list of tuples.
    result = []
    sorted_package_names = sorted(package_versions.keys(), key=lambda name: name.lower())

    for package_name in sorted_package_names:
        versions = sorted(package_versions[package_name], reverse=True)
        # Remember, versions is a list of semantic_version.Version objects.
        # We want strings.
        version_strings = [str(version) for version in versions]
        result.append((package_name, version_strings))
    return result


def ensure_package_exists(repo, tag=None):
    """Given a repo and an optional tag, ensure that a package exists.
    If the package file doesn't exist in PACKAGE_DIRS, one will be built.
    """
    logging.debug("ensure_package_exists: repo={0}, tag={1}".format(repo, tag))
    if tag is None:
        all_tags = get_tags(repo)
        tag = all_tags[0]
        logging.debug("tag calculated as {0}".format(tag))

    name, version = get_package_details(repo, tag)
    logging.debug("name={0} version={1}".format(name, version))

    # If we already have this package, we need to do nothing.
    filename = "{0}-{1}.tar.gz".format(name, version)
    package_file = os.path.join(settings.PACKAGES_DIR, filename)
    if os.path.exists(package_file):
        return ("exists", filename)

    build(repo, tag)
    return ("built", filename)


def get_tags(repo):
    """Return a (sorted) list of all tags.
    The sorting is done using the semantic versioning scheme and is in
    descending order.
    """
    cmd = "git ls-remote --tags {0}".format(repo)
    process = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
    output = process.stdout.read()

    lines = output.split("\n")
    tags = []
    for raw_line in lines:
        if not raw_line:
            continue
        line = raw_line.strip()
        parts = line.split("\t")
        if len(parts) < 2:
            continue

        commit = parts[0]
        ref = parts[1]

        if ref.endswith("^{}"):
            continue

        tags.append(ref.replace("refs/tags/", ""))

    tags.sort(key=lambda tag: get_version(tag), reverse=True)

    return tags


def get_version(tag):
    """Convert a git tag into a tuple of three numbers.
    It assumes that a tag is of the form major, minor, patch.
    """
    # This is most likely to be the leaving 'v'.
    if tag.startswith("v"):
        tag = tag[1:]

    try:
        version = semantic_version.Version(tag)
    except ValueError:
        version = tag
    return version


def get_package_details(repo, branch):
    """Inspect the setup.py file and get the python package name.
    """
    working_dir = tempfile.mkdtemp()

    try:
        # Use -n to ensure we don't checkout any files
        repo = git.Repo.clone_from(repo, working_dir, n=True, branch=branch)
        # Checkout just setup.py
        repo.git.checkout("HEAD", "setup.py")
        return extract_package_details(os.path.join(working_dir, "setup.py"))
    finally:
        shutil.rmtree(working_dir)


def extract_package_details(filename):
    """Given a filename, inspect its contents to find the name=... line and
    return the value of name.
    """
    # TODO! Perhaps mock setuptools.setup and exec the file?
    # It must be better than using a horrible regexp.
    name_pattern = re.compile(r'^.*name( )*=( )*["\'](.*)["\'].*$')
    version_pattern = re.compile(r'^.*version( )*=( )*["\'](.*)["\'].*$')

    name = ""
    version = ""

    with open(filename, "r") as input_file:
        for raw_line in input_file:
            line = raw_line.strip()
            if name == "":
                name_matched = name_pattern.match(line)
                if name_matched:
                    name = name_matched.group(3)

            if version == "":
                version_matched = version_pattern.match(line)
                if version_matched:
                    version = version_matched.group(3)

    return name, version
