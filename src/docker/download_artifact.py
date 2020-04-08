#!/usr/bin/env python3

import argparse
import logging
import os
import shutil

import requests

logging.basicConfig(
    format='%(levelname)s\t%(asctime)s\t\t%(funcName)s\t\t%(message)s',
    level=logging.INFO
)

ENV_API_TOKEN = 'GITHUB_API_TOKEN'
PACKAGE_NAME = 'artifact.zip'

ARTIFACT_NAME = 'yagna.deb'
BRANCH = 'master'
REPO_OWNER = 'golemfactory'
REPO_NAME = 'yagna'
WORKFLOW_NAME = 'Build .deb'

parser = argparse.ArgumentParser()
parser.add_argument('-a', '--artifact', default=ARTIFACT_NAME)
parser.add_argument('-b', '--branch', default=BRANCH)
parser.add_argument('-t', '--token', default=os.environ[ENV_API_TOKEN])
parser.add_argument('-w', '--workflow', default=WORKFLOW_NAME)
args = parser.parse_args()

BASE_URL = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}'
session = requests.Session()
session.headers['Authorization'] = f'token {args.token}'

def get_workflow(workflow_name: str) -> dict:
    url = f'{BASE_URL}/actions/workflows'
    logging.info('fetching workflows. url=%s', url)
    response = session.get(f'{BASE_URL}/actions/workflows')
    response.raise_for_status()

    workflows = response.json()['workflows']
    return next(filter(lambda w: w['name'] == workflow_name, workflows))

def get_latest_run(workflow_id: str) -> dict:
    url = f'{BASE_URL}/actions/workflows/{workflow_id}/runs'
    logging.info('fetching worflow runs. url=%s', url)
    response = session.get(url)
    response.raise_for_status()

    runs = response.json()['workflow_runs']
    latest_run = next(filter(
        lambda r: r['conclusion'] == 'success' and r['head_branch'] == BRANCH,
        runs
    ))
    return latest_run

def download_artifact(artifacts_url: str, artifact_name: str):
    logging.info('fetching artifacts. url=%s', artifacts_url)
    response = session.get(artifacts_url)
    response.raise_for_status()
    artifacts = response.json()['artifacts']
    artifact = next(filter(lambda a: a['name'] == artifact_name, artifacts))

    logging.info('found matching artifact. artifact=%s', artifact)
    archive_url = artifact['archive_download_url']
    with session.get(archive_url, stream=True) as response:
        response.raise_for_status()
        logging.info('downloading artifact. url=%s', archive_url)
        with open(PACKAGE_NAME, 'wb') as fd:
            shutil.copyfileobj(response.raw, fd)

    logging.info('extracting zip archive. path=%s', PACKAGE_NAME)
    shutil.unpack_archive(PACKAGE_NAME, format='zip')
    logging.info('extracted package. path=%s', artifact_name)

if __name__ == '__main__':
    logging.info(
        'workflow_name=%s, artifact_name=%s', args.workflow, args.artifact)

    workflow = get_workflow(args.workflow)
    last_run = get_latest_run(workflow['id'])
    download_artifact(
        last_run['artifacts_url'],
        args.artifact
    )
