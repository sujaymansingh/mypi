"""This has a flask app that exposes endpoints that allow for fetching
and building of packages.

Usage:
    mypi run-debug [--host=<h>] [--port=<p>]
    mypi (-h | --help)

Options:
    -h --help              Show this screen
    --host=<h>             The host on which to run [Default: 0.0.0.0]
    --port=<p>             The port on which to run [Default: 5000]
"""
import logging
import os

import docopt
import flask

from mypi import package_util
from mypi import settings


template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
app = flask.Flask(__name__, template_folder=template_folder, static_folder=static_folder)


@app.route("/<package_file>.tar.gz")
def return_package_file(package_file):
    """Return a .tar.gz file within PACKAGES_DIR
    """
    ensure_initialised()

    # TODO: do we want to sanity check <package_file> for path/escape characters?
    full_path = os.path.join(settings.PACKAGES_DIR, package_file + ".tar.gz")
    if not os.path.exists(full_path):
        return flask.make_response("no file", 404)

    with open(full_path, "r") as package_file:
        response = flask.Response(package_file.read(), mimetype="application/gzip")
        return response


@app.route("/ensure/github/<org>/<repo>", methods=["POST"])
@app.route("/ensure/github/<org>/<repo>/<tag>", methods=["POST"])
def ensure_package_exists(org, repo, tag=None):
    """Given a github org, repo (and optionally a tag) ensure that a package
    file exists.
    """
    ensure_initialised()

    if repo.endswith(".git"):
        repo = repo[:-4]
    github_url = "git@github.com:{0}/{1}.git".format(org, repo)

    status, filename = package_util.ensure_package_exists(github_url, tag=tag)
    return flask.make_response("{1} {0}".format(status, filename), 200)


@app.route("/")
def index():
    ensure_initialised()
    raw_packages = package_util.get_all_packages()
    packages = [expand_into_dict(raw_package) for raw_package in raw_packages]

    return flask.render_template(
        "index.html",
        packages=packages,
        title=settings.SITE_TITLE,
        url_base=settings.SITE_URL_BASE
    )


def expand_into_dict(raw_package):
    """Take a raw tuple of (name, versions) and return a dict that is easier
    to use.
    >>> expand_into_dict(('mypi', ['1.0.0', '0.8.8']))
    {'name': 'mypi', 'versions': [{'url': '/mypi-1.0.0.tar.gz', 'name': '1.0.0'}, {'url': '/mypi-0.8.8.tar.gz', 'name': '0.8.8'}]}
    """
    package_name, version_strings = raw_package
    versions = [
        {"name": v, "url": "/{0}-{1}.tar.gz".format(package_name, v)}
        for v in version_strings
    ]
    return {
        "name": package_name,
        "versions": versions,
    }


def ensure_initialised():
    """Ensure that any package directories exist.
    """
    packages_dir = settings.PACKAGES_DIR
    if os.path.exists(packages_dir) and os.path.isdir(packages_dir):
        return
    os.makedirs(packages_dir)


def main():
    arguments = docopt.docopt(__doc__)

    if arguments.get("run-debug"):
        host = arguments.get("--host")
        port = int(arguments.get("--port"))

        logging.basicConfig(level=logging.DEBUG)
        app.run(host=host, port=port, debug=True)


if __name__ == "__main__":
    main()
