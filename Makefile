install:
	poetry install

project:
	poetry run project

build:
	poetry build

publish:
	poetry publish --dry-run

package-install:
	python3 -m pip install dist/*.whl

package-uninstall:
	python3 -m pip uninstall finalproject-perceva-m25-555 -y

lint:
	poetry run ruff check .
