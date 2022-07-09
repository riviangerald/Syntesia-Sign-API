import pytest

import constants
from evaluator import Evaluator

constants.SECONDS_BETWEEN_ATTEMPTS = 0


def test_ctor():
    evaluator = Evaluator()
    evaluator._Evaluator__stop_queue_process = True
    assert evaluator._Evaluator__number_of_hits == 0

