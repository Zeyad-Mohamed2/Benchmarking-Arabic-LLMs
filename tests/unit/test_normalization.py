"""Unit tests for Arabic orthographic normalization."""

from benchmark_arabic_llms.data.data_preprocessor import normalize_arabic


def test_normalize_diacritics():
    # Text with various Tashkeel/diacritics
    text = "الْعَرَبِيَّةُ لُغَةٌ جَمِيلَةٌ"
    expected = "العربيه لغه جميله"
    assert normalize_arabic(text) == expected


def test_normalize_alef_variants():
    # Various alefs: [إأآا] -> ا
    text = "إبراهيم وأحمد وآمنة"
    expected = "ابراهيم واحمد وامنه"
    assert normalize_arabic(text) == expected


def test_normalize_ta_marbuta_and_alef_maksura():
    # ة -> ه and ى -> ي
    text = "مدرسة القاهرة إلى المستشفى"
    expected = "مدرسه القاهره الي المستشفي"
    assert normalize_arabic(text) == expected


def test_normalize_tatweel_and_whitespace():
    # Kashida / Tatweel removal and extra spaces
    text = "الــــــقـــــاهـــــرة   عاصمة    مصر"
    expected = "القاهرة عاصمة مصر"
    assert normalize_arabic(text) == "القاهره عاصمه مصر"


def test_normalize_empty_and_none():
    assert normalize_arabic("") == ""
    assert normalize_arabic(None) == ""
