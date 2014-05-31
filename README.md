# mypi


## Introduction

```
pip install mypi
python -m mypi run-debug
```

This will start up a server on `localhost:5000`

Now if you have a python project (i.e. one that is build using `setup.py`) on github, you can build it:

```
$ curl -X POST http://localhost:5000/ensure/github/sujaymansingh/mypi
```

This will

* look at the github repository `mypi` (in the organisation/user `sujaymansingh`)
* get the latest tag and clone the code
* run `python setup.py sdist`
* make the build package available at `http://localhost:5000/mypi-0.0.1.tar.gz`

If the package already exists, then it won't build.

You can also build whichever version is at a specific tag.

```
$ curl -X POST http://localhost:5000/ensure/github/sujaymansingh/mypi/v0.0.1
```

## Why would I want to do this?

Perhaps the same reason I need/want to.

At work, we have a lot of private github repositories. Often we bundle up code
into packages that aren't meant to be public (thus can't be on pypi :( ).

So we need a place to host them internally.

Of course, we could manually build the package and upload, but it is easier
to be able to hit an end-point and have it build and uploaded automatically.

A nice example set up:

* jenkins will run tests on any push to master
* if the tests pass, the jenkins job can simply POST to the relevant `mypi` url
* (note jenkins doesn't have to know about tags, it simply tells `mypi` to
   ensure that the latest package is available)
* the latest package is automatically built and uploaded if all is well
* 

## Github auth

It works by running lots of `git` calls under the hood. If you have private repos, then you should set up ssh keys to github.
