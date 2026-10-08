import random

import pytest

from kavach.validators import verhoeff


def test_known_vector_from_reference():
    # Worked example on https://en.wikipedia.org/wiki/Verhoeff_algorithm
    assert verhoeff.check_digit("236") == "3"
    assert verhoeff.is_valid("2363")


def test_wrong_check_digit_is_invalid():
    assert not verhoeff.is_valid("2364")


def test_check_digit_round_trips_on_random_numbers():
    rng = random.Random(0)
    for _ in range(500):
        body = "".join(rng.choice("0123456789") for _ in range(11))
        assert verhoeff.is_valid(body + verhoeff.check_digit(body))


def test_detects_every_single_digit_error():
    body = "23456789012"
    valid = body + verhoeff.check_digit(body)
    for i in range(len(valid)):
        for d in "0123456789":
            if d != valid[i]:
                assert not verhoeff.is_valid(valid[:i] + d + valid[i + 1 :])


def test_detects_every_adjacent_transposition():
    body = "23456789012"
    valid = body + verhoeff.check_digit(body)
    for i in range(len(valid) - 1):
        if valid[i] != valid[i + 1]:
            swapped = valid[:i] + valid[i + 1] + valid[i] + valid[i + 2 :]
            assert not verhoeff.is_valid(swapped)


@pytest.mark.parametrize("bad", ["", "12a4", "12 34", "١٢٣"])
def test_rejects_non_digit_input_without_echoing_it(bad):
    with pytest.raises(ValueError) as exc:
        verhoeff.is_valid(bad)
    if bad:
        assert bad not in str(exc.value)
