from midomtoolbox.ctp.config_script import CTPTraceableTagAction
from midomtoolbox.ctp.elements import CTPFunction, CTPRule
from midomtoolbox.ctp.translation import to_tag_action


def test_to_tag_action():
    tag_action = CTPTraceableTagAction(
        tag_code="00080020",
        tag_name="StudyDate",
        rule=CTPRule(line_elements=[CTPFunction("keep")]),
    )
    translated = to_tag_action(tag_action)
    assert translated  # just don't crash
