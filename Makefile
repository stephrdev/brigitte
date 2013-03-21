pep8:
	flake8 brigitte/${APP} --ignore=E501,E128 --exclude=*migrations*

test:
	coverage run --branch --source=brigitte manage.py test --settings=brigitte_site.test_settings
	coverage html --omit=*migrations* -d tests_report
	coverage report --show-missing --omit=*migrations*

all: pep8 test
