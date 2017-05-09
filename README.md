# Populous - *populate your database with god-like powers*

Populous is a tool for fast and rich data generation. From a description of your schema say how many objects you want, what they should look like, and populate will create them for you!

## Current state
The project is in a very early stage and proof-of-concept state. Please be patient, but don't hesitate to share your thoughts and desires with us in the issues.

## Troubleshooting

### OSX compilation problems

There's currently no pre-compiled package for the ``peloton_bloomfilters`` library, which is a current requirement for populous. To correctly install it in your environment, you're going to:


* install ``gcc`` (via homebrew, for example),
* install the package using the following flags ``ARCHFLAGS="-arch x86_64" CC=/usr/bin/gcc``.

For example, to install locally:

```
ARCHFLAGS="-arch x86_64" CC=/usr/bin/gcc pip install peloton_bloomfilters
```

Or if you want to run the test suite via tox:

```
ARCHFLAGS="-arch x86_64" CC=/usr/bin/gcc tox
```
