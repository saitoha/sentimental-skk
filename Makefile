
PACKAGE_NAME=sentimental-skk
DEPENDENCIES=canossa tff termprop
PYTHON=python
RM=rm -rf

build: test
	$(PYTHON) setup.py sdist
	python2.5 setup.py bdist_egg
	python2.6 setup.py bdist_egg
	python2.7 setup.py bdist_egg

setuptools:
	$(PYTHON) -c "import setuptools" || \
		curl http://peak.telecommunity.com/dist/ez_setup.py | $(PYTHON)

install: setuptools
	$(PYTHON) setup.py install

uninstall:
	for package in $(PACKAGE_NAME) $(DEPENDENCIES); \
	do \
	       	pip uninstall -y $$package; \
       	done
	
clean:
	$(RM) dist/ build/ *.egg-info *.pyc **/*.pyc

test:
	$(PYTHON) setup.py test

update: clean test
	$(PYTHON) setup.py register
	$(PYTHON) setup.py sdist upload
	python2.5 setup.py bdist_egg upload
	python2.6 setup.py bdist_egg upload
	python2.7 setup.py bdist_egg upload

