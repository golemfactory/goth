#!/usr/bin/env python3
import logging

from runner import TestRunner, TestScenario

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(name)-35s %(message)s", level=logging.INFO,
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    TestRunner().run(TestScenario())
