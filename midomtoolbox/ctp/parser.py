from lark import Lark, Transformer
from lark.exceptions import LarkError

from midomtoolbox.ctp.elements import (
    CTPDicomTag,
    CTPFunction,
    CTPFunctionIf,
    CTPRule,
    CTPStringLiteral,
    CTPVariableElement,
    Contains,
    Equals,
    Exists,
    IsBlank,
    Matches,
)
from midomtoolbox.ctp.exceptions import CTPExpressionParseError


class CTPScriptParser:
    """Parses any rule from a CTP config script. Main class to import from this
    module.

    Examples
    --------
    >>> parser = CTPScriptParser()
    >>> rule = parser.parse('@if(root:0075[ANONYMIZER]76,contains,YES)
    {MODIFIED}{@VAR}')

    """

    @staticmethod
    def parse(rule_string):
        """Parses a rule from a CTP config script into a datastructure that
        models the rule's structure

        Parameters
        ----------
        rule_string: str
            A ctp rule as it appears in a CTP config script. For
            example 'if(Modality,equals,MR)'

        Returns
        -------
        CTPRule
            A datastructure that represents the rule

        Raises
        ------
        CTPScriptParserException
            when parsing fails

        """
        try:
            parsed = ctp_script_parser.parse(rule_string)
        except LarkError as e:
            raise CTPScriptParserException(e) from e

        return CTPScriptTransformer().transform(parsed)


ctp_script_parser = Lark(
    r"""
                ctp_rule: function_or_literal+
                function_or_literal: function|string_literal
                string_literal: (LETTER|"."|" "|","|SLASH|DIGIT)+
                SLASH: "/"
                function: "@" function_name "(" params? ")" extra_params?
                function_name: NAME
                params: param ("," param)*
                param: dicom_tag_expression|dicom_tag_name|variable|escaped_string|NAME|NUMBER
                variable.2: "@" NAME
                escaped_string: ESCAPED_STRING
                extra_params: (empty_param|"{" extra_param "}")*
                empty_param: "{}"
                extra_param: (string_literal|function|variable)+

                dicom_tag_expression: modifier? dicom_tag
                modifier: NAME":"
                dicom_tag_name: NAME

                dicom_tag: dicom_group dicom_group
                           | "(" dicom_group "," dicom_group ")"
                           | "[" dicom_group "," dicom_group "]"                           


                dicom_group: FLAT_DICOM_GROUP_4
                            |FLAT_DICOM_GROUP_2 private_creator
                            |private_creator FLAT_DICOM_GROUP_2

                private_creator: "[" NAME "]" 
                FLAT_DICOM_GROUP_4: HEXDIGIT~4
                FLAT_DICOM_GROUP_2: HEXDIGIT~2

                %import common.CNAME -> NAME        
                %import common.HEXDIGIT -> HEXDIGIT
                %import common.NUMBER -> NUMBER                
                %import common.WS_INLINE
                %import common.LETTER -> LETTER
                %import common.DIGIT -> DIGIT
                %import common.ESCAPED_STRING -> ESCAPED_STRING

                %ignore WS_INLINE

            """,
    parser="earley",
    start="ctp_rule",
)


class CTPScriptParserException(Exception):
    pass


class CTPScriptTranformerException(CTPScriptParserException):
    pass


class CTPScriptTransformer(Transformer):
    """Transforms rules like
    '@always()@if(root:007534[RABOUDANONYMIZER],contains,YES){@incrementdate(
    this,@DATEINC)}{else}'
     into a manageable datastructure

    """

    def transform(self, tree):
        """Transform a CTP script parsed with ctp_script_parser into a useful
        datastructure

        Parameters
        ----------
        tree:
            output of ctp_script_parser.parse()

        Returns
        -------
        List[CTPScriptElement]

        Raises
        ------
        CTPScriptTranformerException
            when parsing fails

        """
        try:
            return self._transform_tree(tree)
        except LarkError as e:
            raise CTPScriptTranformerException(e)

    def ctp_rule(self, items):
        return CTPRule(line_elements=items)

    def function_or_literal(self, items):
        return items[0]

    def string_literal(self, items):
        return CTPStringLiteral(content="".join(items))

    def parse_expression(self, expression_list):
        """See what kind of expression this is: equals, exists, isblank"""

        # first argument is either like '00751012' or lie 'root:00751912', or
        # like 'Modality'
        parts = expression_list[0].split(":")
        if len(parts) == 2:
            modifyer, tag = parts
        elif len(parts) == 1:
            modifyer, tag = [None] + parts
        else:
            raise CTPScriptTranformerException(
                f"Expected modifyer:dicomtag but found '{parts}'"
            )
        tag = CTPDicomTag(tag_string=tag, modifier=modifyer)

        # second part of if statement determines the type of comparison
        if len(expression_list) not in [2, 3]:
            msg = (
                f"cannot parse parameters {expression_list} as a valid CTP "
                f"if-statement"
            )
            raise CTPScriptParserException(msg)
        type = expression_list[1]
        if type == "contains":
            # Don't leave any unparsed tokens. If you haven't found the type of
            # something now, just assume it's a
            # string
            compare_with = self.cast_to_string_literal(expression_list[2])
            return Contains(tag=tag, value=compare_with)
        elif type == "equals":
            compare_with = self.cast_to_string_literal(expression_list[2])
            return Equals(tag=tag, value=compare_with)
        elif type == "matches":
            regex = expression_list[2]
            return Matches(tag=tag, regex=regex)

        elif type == "exists":
            return Exists(tag=tag)
        elif type == "isblank":
            return IsBlank(tag=tag)
        else:
            msg = f"could not parse {expression_list} as a CTP expression"
            raise CTPExpressionParseError(msg)

    @staticmethod
    def cast_to_string_literal(object_in):
        """If the incoming object is still an unprocessed lark token, make it
        into a CTPString literal

        For making sure there are no un-parsed tokens left"""
        if isinstance(object_in, str):
            return CTPStringLiteral(object_in)
        else:
            return object_in

    def function(self, items):
        # items could be variable length, but the order is fixed.
        # Trick to assign None to missing items. Make sure it's length 3 and pad
        # out missing with None
        items = (items + [None] * 3)[:3]
        name, params, extra_params = items
        if name == "if":
            if_element = self.parse_expression(expression_list=params)
            then_element, else_element = extra_params
            return CTPFunctionIf(
                rule_if=if_element,
                rule_then=then_element,
                rule_else=else_element,
            )
        else:
            # make sure everything is parsed
            if params:
                params = list(map(self.cast_to_string_literal, params))
            if extra_params:
                extra_params = list(
                    map(self.cast_to_string_literal, extra_params)
                )
            return CTPFunction(
                name=name, params=params, extra_params=extra_params
            )

    def function_name(self, items):
        return str(items[0])

    def params(self, items):
        return items

    def param(self, items):
        return items[0]

    def escaped_string(self, items):
        # param could be an ESCAPED_STRING, which passes the apostrophes as well.
        # I don't want those
        return items[0].replace('"', "")

    def modifier(self, items):
        return str(items[0])

    def dicom_tag(self, items):
        return "".join([str(x) for x in items])

    def dicom_group(self, items):
        return "".join([str(x) for x in items])

    def private_creator(self, items):
        return f"[{str(items[0])}]"

    def dicom_tag_expression(self, items):
        if len(items) == 2:
            modifier = items[0]
            tag_string = items[1]
            return modifier + ":" + tag_string
        else:
            tag_string = items[0]
            return tag_string

    def dicom_tag_name(self, items):
        """keep dicom tag as string, cast to CTPDicomTag higher up the parse tree"""
        return items[0]

    def extra_params(self, items):
        return items

    def empty_param(self, _):
        return CTPStringLiteral(content="")

    def extra_param(self, items):
        return items[0]

    def variable(self, items):
        return CTPVariableElement(name=items[0])


class CTPParsedElement:
    """Any meaningful part of a CTP line"""

    pass


class CTPFunctionElement(CTPParsedElement):
    """Example: @if(root:0075[ANONYMIZER]76,contains,YES)
    {@always()MODIFIED}{@always()REMOVED}"""

    def __init__(self, name, params=None, extra_params=None):
        self.name = name
        self.params = params
        self.extra_params = extra_params

    def __str__(self):
        return f"CTPFunctionElement '{self.name}'"


class CTPDicomTagExpressionElement(CTPParsedElement):
    """Example: root:0075[ANONYMIZER]76,contains,YES"""

    def __init__(self, expression, modifier=None):
        self.expression = expression
        self.modifier = modifier


class CTPDicomTagElement(CTPParsedElement):
    """Example: 0075[ANONYMIZER]76,contains,YES"""

    def __init__(self, expression):
        self.expression = expression
