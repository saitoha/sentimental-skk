
all:

run:
	python sskk/__init__.py
	

install:
	#curl http://peak.telecommunity.com/dist/ez_setup.py | python
	python setup.py install

uninstall:
	rm -rf /Users/user/.pythonz/pythons/CPython-2.7.3/lib/python2.7/site-packages/sentimental_skk*
	rm -f /Users/user/.pythonz/pythons/CPython-2.7.3/bin/sskk
	yes | pip uninstall tff sentimental-skk
	
clean:
	rm -rf dist/ build/ sentimental_skk.egg-info
	rm **/*.pyc

update:
	python setup.py register
	python setup.py sdist upload
	python2.6 setup.py bdist_egg upload
	python2.7 setup.py bdist_egg upload

