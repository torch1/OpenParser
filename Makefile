URL=http://pencil.org/

init:
	pip install -r requirements.txt

parse:
	python openparser/parse.py $(URL)

test:
	pytest tests

.PHONY: init test
