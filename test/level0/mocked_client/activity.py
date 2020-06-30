import json
import time
import os
from pathlib import Path

from openapi_activity_client import (
    ApiClient,
    Configuration,
    RequestorControlApi,
    RequestorStateApi,
    ExeScriptRequest,
)


def level0_activity(agreement_id):
    # INIT
    config = Configuration(host=f"{os.environ['YAGNA_API_URL']}/activity-api/v1")
    config.access_token = os.environ["APP_KEY"]

    api_client = ApiClient(config)
    req_api = RequestorControlApi(api_client)
    state_api = RequestorStateApi(api_client)
    print(f"Init completed, connected to {config.host}")

    # Create Activity
    activity_id = req_api.create_activity(agreement_id)
    print(f"created activity. id={activity_id}")

    state = state_api.get_activity_state(activity_id)
    print(f"state. result={state}")
    # i. PROVIDER

    # provider.event.waitFor(LogEvent, event => matches "ExeUnit start log regexp")
    time.sleep(2.0)
    # ii. REQUESTOR

    my_path = os.path.abspath(os.path.dirname(__file__))
    exe_script_txt = Path(my_path + "/../asset/exe_script.json").read_text()

    print(f"exe_script read. contents={exe_script_txt}")

    batch_id = req_api.call_exec(activity_id, ExeScriptRequest(exe_script_txt))
    print(f"exe_script executed. batch_id={batch_id}")

    # time.sleep(5.)

    commands_cnt = len(json.loads(exe_script_txt))
    state = state_api.get_activity_state(activity_id)
    print(f"state. result={state}")
    results = req_api.get_exec_batch_results(activity_id, batch_id)
    print(f"poll batch results. result={results}")

    while len(results) < commands_cnt:
        time.sleep(1.0)
        state = state_api.get_activity_state(activity_id)
        print(f"state. result={state}")
        results = req_api.get_exec_batch_results(
            activity_id, batch_id
        )  # TODO: requestor.events.waitUntil(ExecScriptCommandFinishedEvent)
        print(f"poll batch results. result={results}")

    req_api.destroy_activity(activity_id)
