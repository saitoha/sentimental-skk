
PACKAGE_NAME=sentimental-skk
DEPENDENCIES=canossa tff termprop
PYTHON=python
PYTHON25=python2.5
PYTHON26=python2.6
PYTHON27=python2.7
SETUP_SCRIPT=setup.py
RM=rm -rf
PIP=pip

.PHONY: smoketest nosetest build setuptools install uninstall clean update

all: build

setup_environment:
	if test -d tools; do \
		ln -f tools/gitignore .gitignore \
		ln -f tools/vimprojects .vimprojects \
    fi

build: update_license_block smoketest
	$(PYTHON) $(SETUP_SCRIPT) sdist
	$(PYTHON25) $(SETUP_SCRIPT) bdist_egg
	$(PYTHON26) $(SETUP_SCRIPT) bdist_egg
	$(PYTHON27) $(SETUP_SCRIPT) bdist_egg

update_license_block:
	#chmod +x update_license
	#find . -type f | grep '\(.py\|.c\)$$' | xargs ./update_license

setuptools:
	$(PYTHON) -c "import setuptools" || \
		curl http://peak.telecommunity.com/dist/ez_$(SETUP_SCRIPT) | \
		$(PYTHON)

install: smoketest setuptools
	$(PYTHON) $(SETUP_SCRIPT) install

uninstall:
	for package in $(PACKAGE_NAME) $(DEPENDENCIES); \
	do \
		$(PIP) uninstall -y $$package; \
	done

clean:
	for name in dist build *.egg-info *.egg htmlcov cover; \
		do find . -type d -name $$name || true; \
	done | xargs $(RM)
	for name in *.pyc *.o; \
		do find . -type f -name $$name || true; \
	done | xargs $(RM)

test: smoketest nosetest

smoketest:
	$(PYTHON25) $(SETUP_SCRIPT) test
	$(PYTHON26) $(SETUP_SCRIPT) test
	$(PYTHON27) $(SETUP_SCRIPT) test

nosetest:
	if $$(which nosetests); \
	then \
	    nosetests --with-doctest \
	              --with-coverage \
	              --cover-html \
	              --cover-package=sskk; \
	fi

update: clean test
	$(PYTHON) $(SETUP_SCRIPT) register
	$(PYTHON) $(SETUP_SCRIPT) sdist upload
	$(PYTHON25) $(SETUP_SCRIPT) bdist_egg upload
	$(PYTHON26) $(SETUP_SCRIPT) bdist_egg upload
	$(PYTHON27) $(SETUP_SCRIPT) bdist_egg upload

cleanupdate: update
	ssh zuse.jp "rm -rf $(PACKAGE_NAME)"
	ssh zuse.jp "git clone git@github.com:saitoha/$(PACKAGE_NAME) --recursive"
	ssh zuse.jp "make test -C $(PACKAGE_NAME)"
	ssh zuse.jp "cd $(PACKAGE_NAME) && $(PYTHON26) $(SETUP_SCRIPT) bdist_egg upload"
	ssh zuse.jp "cd $(PACKAGE_NAME) && $(PYTHON27) $(SETUP_SCRIPT) bdist_egg upload"

