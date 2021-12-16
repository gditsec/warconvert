.PHONY: docs
init:
	python3 -m pip install 'twine>=3.6.0'
	python3 -m pip install --upgrade build
	python3 -m pip install -r requirements.txt

clean:
	rm -rf dist/

build:
	python3 -m build

publish-test:
	make clean
	python3 -m twine upload --repository testpypi dist/*

publish:
	make clean
	python3 -m twine upload dist/*
