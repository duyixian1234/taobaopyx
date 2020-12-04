lint:
	pylint taobaopyx
	mypy taobaopyx
	isort --check --diff taobaopyx

test:
	pytest --cov=taobaopyx --cov-fail-under=90 -svv tests

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test:
	rm -f .coverage
	rm -fr .pytest_cache

clean: clean-pyc clean-test