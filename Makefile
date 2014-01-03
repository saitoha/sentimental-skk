
PACKAGE_NAME=$(BASENAMEsentimental-skk
DEPENDENCIES=canossa tff termprop
PYTHON=python
RM=rm -rf

.PHONY: smoketest nosetest build setuptools install uninstall clean update

build: update_license_block smoketest
	$(PYTHON) setup.py sdist
	python2.5 setup.py bdist_egg
	python2.6 setup.py bdist_egg
	python2.7 setup.py bdist_egg

update_license_block:
	#chmod +x update_license
	#find . -type f | grep '\(.py\|.c\)$$' | xargs ./update_license

setuptools:
	$(PYTHON) -c "import setuptools" || \
		curl http://peak.telecommunity.com/dist/ez_setup.py | $(PYTHON)

install: smoketest setuptools
	$(PYTHON) setup.py install

uninstall:
	for package in $(PACKAGE_NAME) $(DEPENDENCIES); \
	do \
		pip uninstall -y $$package; \
	done

clean:
	for name in dist build *.egg-info htmlcov *.pyc *.o; \
		do find . -type d -name $$name || true; \
	done | xargs $(RM)

smoketest:
	$(PYTHON) setup.py test

nosetest:
	if $$(which nosetests); \
	then \
	    nosetests --with-doctest \
	              --with-coverage \
	              --cover-html \
	              --cover-package=sskk; \
	else \
	    $(PYTHON) setup.py test; \
	fi

update: clean smoketest
	$(PYTHON) setup.py register
	$(PYTHON) setup.py sdist upload
	python2.5 setup.py bdist_egg upload
	python2.6 setup.py bdist_egg upload
	python2.7 setup.py bdist_egg upload

