#
# Shiji API build tools
#
SHELL=/bin/bash
PROJECT=Shiji API
ROOT_DIR=/git/shiji
COPYRIGHT=(C)2015 DigiTar, All Rights Reserved
AUTHOR_EMAIL=williamsjj@digitar.com

prepare_env: venv/bin/activate
venv/bin/activate: requirements.txt
	test -d venv || virtualenv venv
	venv/bin/pip install -U -I -r requirements.txt
	touch venv/bin/activate

# Build Eggs
clean:
	find . -name "*.pyc" -exec rm '{}' ';'

# Run Tests
test_ci: prepare_env clean
	venv/bin/pip install $(ROOT_DIR)
	mkdir -p $(CIRCLE_TEST_REPORTS)/trial
	PYTHONPATH=$(ROOT_DIR) venv/bin/trial --reporter=subunit shiji.tests | venv/bin/subunit-1to2 | venv/bin/subunit2junitxml --no-passthrough --output-to=$(CIRCLE_TEST_REPORTS)/trial/junit.xml
	[[ "0" != `xmlstarlet sel -T -t -m '//testsuite/@tests' -v '.' -n $(CIRCLE_TEST_REPORTS)/trial/junit.xml` ]]

test: prepare_env clean
	venv/bin/pip install $(ROOT_DIR)
	PYTHONPATH=$(ROOT_DIR) venv/bin/trial shiji.tests

test_one: prepare_env clean
	venv/bin/pip install $(ROOT_DIR)
	PYTHONPATH=$(ROOT_DIR) venv/bin/trial $(TEST_NAME)

coverage:
	venv/bin/pip install $(ROOT_DIR)
	PYTHONPATH=$(ROOT_DIR) venv/bin/coverage run --omit='venv/lib/python2.7/site-packages/*,/Library/Python/2.7/site-packages/*,/Library/Python/2.6/site-packages/*,/System/Library/Frameworks/Python.framework/*,$(ROOT_DIR)/shiji/_trial_temp/*,$(ROOT_DIR)/shiji/tests/*,$(ROOT_DIR)/shiji/dummy_api/*,$(ROOT_DIR)/shiji/testutil/*' --branch /usr/bin/trial shiji.tests
