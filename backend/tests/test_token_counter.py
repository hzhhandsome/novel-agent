from app.services.token_counter import TokenCounter, count_tokens


class FakeTokenizer:
    name_or_path = "fake-tokenizer"

    def encode(self, text, add_special_tokens=False):
        return text.split()


def test_count_tokens_uses_deterministic_fallback_by_default():
    result = count_tokens("abcdefgh")

    assert result.tokens == 4
    assert result.chars == 8
    assert result.counter_name == "heuristic_chars_div_2"
    assert result.is_fallback is True


def test_token_counter_uses_injected_tokenizer():
    counter = TokenCounter(tokenizer=FakeTokenizer())

    result = counter.count("one two three")

    assert result.tokens == 3
    assert result.chars == 13
    assert result.counter_name == "fake-tokenizer"
    assert result.is_fallback is False
