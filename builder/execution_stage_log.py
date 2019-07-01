import os
import datetime
import requests

GRAPHQL_URL = os.environ['BOLT_GRAPHQL_URL']
EXECUTION_ID = os.environ['BOLT_EXECUTION_ID']
HASURA_TOKEN = os.environ['BOLT_HASURA_TOKEN']


def send_stage_log(message, stage, level='info'):
    ts = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
    query = '''
    mutation ($log_entry:execution_stage_log_insert_input!) {
        insert_execution_stage_log(objects:[$log_entry]) { affected_rows }
    }
    '''
    body = {
        'query': query,
        'variables': {
            'log_entry': {
                'timestamp': ts,
                'stage': stage,
                'level': level,
                'msg': message,
            }
        }
    }
    headers = {'Authorization': f'Bearer {HASURA_TOKEN}'}
    response = requests.post(GRAPHQL_URL, json=body, headers=headers)
    assert response.json().get('data') == {'insert_execution_stage_log': {'affected_rows': 1}}
    response.raise_for_status()
