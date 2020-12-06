from datetime import datetime
from taobaopyx.taobao import default_value_to_str, VALUE_TO_STR


def test_to_str():
    assert default_value_to_str(1) == "1"
    assert VALUE_TO_STR[datetime](datetime(2020, 1, 1)) == "2020-01-01 00:00:00"
    assert VALUE_TO_STR[str]("aaa") == "aaa"
    assert VALUE_TO_STR[float](1.234) == "1.23"
    assert VALUE_TO_STR[bool](True) == "true"
