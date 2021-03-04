"""Helper functions for running Activity."""

import json

from goth.runner.provider import ProviderProbeWithLogSteps
from goth.runner.requestor import RequestorProbeWithApiSteps


async def run_activity(
    requestor: RequestorProbeWithApiSteps,
    provider: ProviderProbeWithLogSteps,
    agreement_id: str,
    exe_script: dict,
):
    """Run single Activity from start to end."""

    activity_id = await requestor.create_activity(agreement_id)
    await provider.wait_for_exeunit_started()

    batch_id = await requestor.call_exec(activity_id, json.dumps(exe_script))
    await requestor.collect_results(activity_id, batch_id, len(exe_script), timeout=30)

    await requestor.destroy_activity(activity_id)
    await provider.wait_for_exeunit_finished()
