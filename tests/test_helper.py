from normalizer import helper

def test_choose_jina_version(mocker):
    mocker.patch('normalizer.helper.get_jina_latest_version', return_value='2.0.0rc10')

    assert helper.choose_jina_version('2.0.0rc11') == '2.0.0rc10'
    assert helper.choose_jina_version('2.0.0rc9') == '2.0.0rc9'
    assert helper.choose_jina_version('master') == 'master'
