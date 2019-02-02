import os
import tempfile

from click.testing import CliRunner
import click
import pytest

from transformation_invariant_image_search import main



@pytest.fixture
def client():
    app = main.create_app()
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['TESTING'] = True
    client = app.test_client()

    with app.app_context():
        #  flaskr.init_db()
        pass

    yield client

    os.close(db_fd)
    os.unlink(app.config['DATABASE'])


def test_empty_db(client):
    """Start with a blank database."""

    rv = client.get('/')
    assert b'Home - Transformation Image Search' in rv.data


def test_help():
    runner = CliRunner()
    result = runner.invoke(main.cli, ['--help'])
    assert result.exit_code == 0
    assert 'Usage:' in result.output


def test_version():
    runner = CliRunner()
    result = runner.invoke(main.cli, ['--version'])
    assert result.exit_code == 0
    #  assert '' in result.output
