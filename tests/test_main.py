import json
import os
import shutil
import tempfile

from click.testing import CliRunner
from flask import current_app
import click
import pytest

from transformation_invariant_image_search import main


@pytest.fixture
def client():
    db_fd, config_db = tempfile.mkstemp()
    image_fd = tempfile.mkdtemp()
    db_uri = 'sqlite:///{}'.format(config_db)
    app = main.create_app(db_uri=db_uri, image_dir=image_fd)
    app.config['DATABASE'] = config_db
    app.config['TESTING'] = True
    client = app.test_client()

    yield client

    os.close(db_fd)
    os.unlink(app.config['DATABASE'])
    shutil.rmtree(image_fd)


def test_empty_db(client):
    """Start with a blank database."""
    rv = client.get('/')
    assert b'Home - Transformation Invariant Image Search' in rv.data


def test_checksum_get(client):
    """test checksum with a blank database."""
    url = '/api/checksum'
    rv = client.get(url)
    assert rv.get_json() == []


def test_checksum_post(client):
    """Start with a blank database."""
    csm_value = '54abb6e1eb59cccf61ae356aff7e491894c5ca606dfda4240d86743424c65faf'
    url = '/api/checksum'
    exp_dict = dict(value=csm_value, id=1, ext='png', trash=False)
    rv = client.post(url, data=dict(value=csm_value, ext='png'))
    assert rv.get_json() == exp_dict
    rv = client.get(url)
    assert rv.get_json() == [exp_dict]


def test_image_post(client):
    url = '/api/image'
    filename = 'fullEndToEndDemo/inputImages/cat_original.png'
    csm_value = '54abb6e1eb59cccf61ae356aff7e491894c5ca606dfda4240d86743424c65faf'
    ext = 'png'
    exp_dict = dict(id=1, value=csm_value, ext=ext, trash=False)
    rv = client.post(url)
    assert rv.get_json()['error']
    file_data = {'file': open(filename, 'rb')}
    rv = client.post(url, data=file_data)
    post_exp_dict = exp_dict.copy()
    post_exp_dict['url'] = ['http://localhost/i/{}.{}'.format(csm_value, ext)]
    assert rv.get_json() == post_exp_dict
    image_dir = client.application.config.get('IMAGE_DIR')
    exp_dst_file = os.path.join(image_dir, csm_value[:2], '{}.{}'.format(csm_value, ext))
    assert os.path.isfile(exp_dst_file)
    rv = client.get(url)
    assert rv.get_json() == [exp_dict]


@pytest.mark.parametrize(
    'args,word',
    [
        ('--help', 'Usage:'),
        ('--version', 'Transformation Invariant Image Search')
    ]
)
def test_cli(args, word):
    runner = CliRunner()
    result = runner.invoke(main.cli, [args])
    assert result.exit_code == 0
    if word is not None:
        assert word in result.output
