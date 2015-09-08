
# Copyright 2015, Marc Murray <murraym@moh.gov.jm>
# Date Aug 3, 2015
# configure initdb install

SETUP_BUILD = "python setup.py sdist"
SETUP_DIRS = "dist build"

.PHONY: clean dist build upload publish

all: dist

clean:
	-rm -r modules/*/dist
	-rm -r modules/*/*.egg-info
	-find modules/ -name '*.pyc' -delete

clean-all: clean
	-rm -r dist/

build:
	find modules/ -name 'setup.py' -execdir python '{}' sdist \;

upload:
	find modules/ -name 'setup.py' -execdir python '{}' sdist upload -r local \;

publish:
	find modules/ -name 'setup.py' -execdir python '{}' sdist upload -r nhin -s -i murraym@moh.gov.jm \;

dist: build
	mkdir dist
	-cp modules/*/dist/*.tar.gz dist/
	cd dist; tar -zcf ../healthjm.tar.gz ./*.tar.gz

# package: pkg-base pkg-encounter pkg-
