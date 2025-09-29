class CTPScriptParseError(Exception):
    pass


class CTPScriptProcessIsNoActionError(CTPScriptParseError):
    pass


class CTPScriptDicomTagParseError(CTPScriptParseError):
    pass


class CTPExpressionEvaluationError(CTPScriptParseError):
    pass


class CTPExpressionParseError(CTPScriptParseError):
    pass
