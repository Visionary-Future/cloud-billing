.PHONY: clean build publish-test publish

clean:
	rm -rf dist/ build/ *.egg-info

build: clean
	python -m build

publish-test: build
	python -m twine upload --repository testpypi dist/*

publish: build
	python -m twine upload dist/*
