import pytest

from kavach.context import has_context, keywords_for
from kavach.types import EntityType

BANK = EntityType.BANK_ACCOUNT
NUM = "123456789012"


def check(text: str, entity_type=BANK) -> bool:
    start = text.index(NUM)
    return has_context(text, start, start + len(NUM), entity_type)


@pytest.mark.parametrize(
    "text",
    [
        f"My account number is {NUM}",
        f"A/C No. {NUM}",
        f"Please credit to {NUM} today",
        f"{NUM} is my savings account",
        f"mera khata number {NUM} hai",
        f"KHATA {NUM}",
        f"मेरा खाता संख्या {NUM} है",
        f"बैंक खाते {NUM}",
    ],
)
def test_finds_keywords_in_english_hinglish_and_devanagari(text):
    assert check(text)


@pytest.mark.parametrize(
    "text",
    [
        f"Order {NUM} has shipped",
        f"Accepted {NUM}",  # "acc" must be a whole word
        f"Discount code {NUM}",
        f"{NUM}",
        f"Bankura {NUM}",  # "bank" must be a whole word
    ],
)
def test_no_keyword(text):
    assert not check(text)


def test_keyword_outside_window_is_ignored():
    far = "account " + "x" * 60 + " " + NUM
    near = "account " + "x" * 10 + " " + NUM
    assert not check(far)
    assert check(near)


def test_span_itself_is_not_searched():
    text = "account"
    assert not has_context(text, 0, len(text), BANK)


def test_keywords_merge_english_and_hindi():
    words = keywords_for(BANK)
    assert "account" in words
    assert "khata" in words
    assert "खाता" in words


def test_every_entity_type_has_keywords():
    for entity_type in EntityType:
        assert keywords_for(entity_type), entity_type
