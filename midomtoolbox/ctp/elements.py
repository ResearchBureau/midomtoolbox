"""Representations of all parts of a CTP configuration script"""

import re
from abc import ABC, abstractmethod
from typing import List, Optional

from pydicom import Dataset
from pydicom.datadict import tag_for_keyword
from pydicom.tag import BaseTag

from midomtoolbox.ctp.exceptions import (
    CTPExpressionEvaluationError,
    CTPScriptDicomTagParseError,
)


class CTPLinePrintable(ABC):
    """A logical part of a single line in a CTP script that can be printed as a
    string.

    Could be some kind of function or a parameter or just a string. Made this
    separate class to have a print
    function for CTP script format that is different from the default __str__()
    method

    """

    @abstractmethod
    def ctp_script_string(self):
        """The representation of this element in CTP script
        Returns
        -------
        str:
            how this element would appear in a CTP script
        """
        pass


class CTPConfigParameter:
    """A parameter used in the rest of the script for substitutions"""

    def __init__(self, name, value):
        """
        Parameters
        ----------
        name: str
            name of this parameter. This can be used as a key for substitution in
             other parts of the script
        value: str
            The value that this parameter takes. The value that is substituted
            should the key be found in other parts
            of the script
        """
        self.name = name
        self.value = value

    def __str__(self):
        return f"Parameter {self.name}: '{self.value}'"


class CTPConfigScriptContext:
    """Parameters and DICOM tag values that can modify the behaviour of a CPT
    script

    What A CTP config script does can be modified by parameters in the
    script itself, or by values in the DICOM
    file that is being processed. This class holds both
    """

    def __init__(
        self,
        dicom_values: Dataset,
        parameters: Optional[List[CTPConfigParameter]] = None,
    ):
        """

        Parameters
        ----------
        dicom_values: :obj:pydicom.Dataset
            Collection of dicom tags and values to stand in for the file
            that is being processed
        parameters: List[CTPConfigParameter], optional
            List of CTP script parameters. Defaults to empty list
        """
        self.dicom_values = dicom_values
        if not parameters:
            parameters = []
        self.parameters = parameters


class Resolvable:
    """A mixin class for any object that can be simplified by applying a
    CPT context to it.
    All Resolvables have a resolve(context) method

    Examples
    --------
    A rule '@if(0075[PRIVATECREATOR]12, equals, foo){@PARAM1}{NO}', could
    be resolved to just 'NO'
    if [PRIVATECREATOR] can be resolved and the tag does not equal 'foo'

    """

    def resolve(self, context: CTPConfigScriptContext):
        """Resolves or simplifies this as far as possible given the context.
        Chains resolution by calling
        resolve on all attributes of this object that are resolvable themselves.

        Parameters
        ----------
        context: :obj:`CTPConfigScriptContext`
            resolve using this context

        Returns
        -------
        Nothing, just changes internal resolvable attributes
        """
        public_attribute_names = [
            x for x in dir(self) if not x.startswith("__")
        ]
        resolvable_attribute_names = [
            x
            for x in public_attribute_names
            if isinstance(getattr(self, x), Resolvable)
        ]
        for name in resolvable_attribute_names:
            resolvable = getattr(self, name)
            resolvable.resolve(context)


class CTPRule(Resolvable):
    def __init__(self, line_elements: List[CTPLinePrintable]):
        """The complete set of actions to be taken for a single tag.
        The entire contents of the <e> </e> tag in a CTP script

        Parameters
        ----------
        line_elements: List[CTPLinePrintable]
            collection of functions and literals that make up this rule

        Examples
        --------
        A rule could be a single function like this:
            @if(0075[ANONYMIZER]80,contains,YES){@skip()}{@keep()}

        Or a function and a literal string like this:
        @if(0075[ANONYMIZER]80,contains,YES){YES}{}somestring

        Or any combination of literal strings and functions
        """
        self.line_elements = line_elements

    def resolve(self, context: CTPConfigScriptContext):
        """Resolve all line elements

        Parameters
        ----------
        context: :obj:`CTPConfigScriptContext`
            resolve using this context

        Returns
        -------
        Nothing, just changes internal resolvable attributes
        """

        resolvable_elements = [
            x for x in self.line_elements if isinstance(x, Resolvable)
        ]
        for element in resolvable_elements:
            element.resolve(context)

    def contains_skip_command(self):
        """Would this rule be interpreted as @skip() by CTP?

        In CTP, when the command @skip() is given, all further excution
        of the script file is halted.

        """
        functions = [
            x for x in self.line_elements if isinstance(x, CTPFunction)
        ]

        for func in functions:
            # skip only happens in two cases. If an @if rule has resolved to @skip()..
            if hasattr(func, "resolved_value"):
                if hasattr(func.resolved_value, "name"):
                    return func.resolved_value.name == "skip"
            # or if the function is a @skip itself..
            return func.name == "skip"

        return False

    def ctp_script_string(self):
        return "".join([x.ctp_script_string() for x in self.line_elements])


class CTPFunction(Resolvable, CTPLinePrintable):
    """A function within a CTP action
    Example @if(this=1){then}{else}, or @always(), or @replace()
    """

    def __init__(self, name, params=None, extra_params=None):
        """

        Parameters
        ----------
        name: str
            the name of this function
        params: List[CTPLinePrintable], optional
            list of parameters to this function, defaults to empty list
        extra_params: List[CTPLinePrintable], optional
            list of extra parameters. It is not quite clear to me what the
            rationale is in CTP scripts to have
            parameters and extra parameters. But let's not split hairs.
            defaults to empty list

        """
        if not params:
            params = []
        if not extra_params:
            extra_params = []
        self.name = name
        self.params = params
        self.extra_params = extra_params

    def __str__(self):
        return f"Function {self.name}"

    def resolve(self, context: CTPConfigScriptContext):
        """By default, resolve() resolves all direct attributes that are of type
        Resolvable. This function contains two lists of resolvables: params and
        extra_params. Resolve each item in these instead
        """

        for param in [x for x in self.params if isinstance(x, Resolvable)]:
            param.resolve(context)
        for extra_param in [
            x for x in self.extra_params if isinstance(x, Resolvable)
        ]:
            extra_param.resolve(context)

    def ctp_script_string(self):
        """Something like @if(this, equals, that){do_A}{do_B}"""
        if self.params:
            params_string = (
                f"({','.join([x.ctp_script_string() for x in self.params])})"
            )

        else:
            params_string = "()"

        if self.extra_params:
            extra_params_string = "".join(
                ["{" + x.ctp_script_string() + "}" for x in self.extra_params]
            )
        else:
            extra_params_string = ""

        return f"@{self.name}{params_string}{extra_params_string}"


class CTPFunctionIf(CTPFunction, Resolvable):
    """a function like like @if{this}{then do A}{else do B}"""

    def __init__(self, rule_if, rule_then, rule_else):
        """

        Parameters
        ----------
        rule_if: CTPExpression
            If this expression evaluates to true
        rule_then: CTPLinePrintable
            Then this should happen
        rule_else: CTPLinePrintable
            If expression is not true, this should happen
        """
        super().__init__(name="if")

        # Fill in parameters like this and expose rule_if etc. as function
        # below to remain consistent with CTPFunction()
        # signature
        self.params = [rule_if]
        self.extra_params = [rule_then, rule_else]
        self.resolved_value = None

    @property
    def rule_if(self):
        return self.params[0]

    @property
    def rule_then(self):
        return self.extra_params[0]

    @property
    def rule_else(self):
        return self.extra_params[1]

    def __str__(self):
        return (
            f"Function if {str(self.rule_if)} then {str(self.rule_then)}, "
            f"else {str(self.rule_else)}"
        )

    def resolve(self, context):
        """Rather then just simplify all the terms, also try to resolve this
        if statement
        """
        # simplify all terms as far as possible
        super().resolve(context)

        # resolve this if statement
        try:
            expression_is_true = self.rule_if.is_true(context)
        except CTPExpressionEvaluationError:
            # its not possible to determine whether this is true. Stop trying
            # to resolve this.
            self.resolved_value = None
        else:
            if expression_is_true:
                self.resolved_value = self.rule_then
            else:
                self.resolved_value = self.rule_else

    def ctp_script_string(self):
        """Something like @if(this, equals, that){do_A}{do_B}"""
        if self.resolved_value:
            return self.resolved_value.ctp_script_string()
        else:
            return (
                "@if"
                + self.rule_if.ctp_script_string()
                + "{"
                + self.rule_then.ctp_script_string()
                + "}"
                + "{"
                + self.rule_else.ctp_script_string()
                + "}"
            )


class CTPStringLiteral(CTPLinePrintable):
    """Just a string, interpret as string"""

    def __init__(self, content):
        self.content = content

    def __str__(self):
        return self.content

    def ctp_script_string(self):
        return self.content


class CTPDicomTag(Resolvable, CTPLinePrintable):
    """A description of a DICOM tag in a CTP config script.

    This might be direct dicom tag like, '101011e8', or something that
    needs resolving like '0075[ANONYMIZER]81', or a dicom tag
    name like 'PatientID'

    """

    def __init__(self, tag_string, modifier=None):
        """

        Parameters
        ----------
        tag_string: str
            dicom tag like, '101011e8', or something that needs resolving
            like '0075[ANONYMIZER]81'
        modifier: str
            CTP uses 'root:' in front of a tag sometimes to denote that tag
            cannot be applied inside tag groups
        """
        self.tag_string = tag_string
        self.modifier = modifier
        self.tag_name = None

    def __str__(self):
        return self.tag_string

    @staticmethod
    def hex_to_int(hex_string):
        """Convert hex string like '20f' to int"""
        return int("0x" + hex_string, 16)

    def resolve(self, context: CTPConfigScriptContext):
        """Try to a CTP dicom tag into a canonical hex string like '00751081'.

        Parameters
        ----------
        context :obj:`CTPConfigScriptContext`
            The context to use to resolve this tag

        Raises
        ------
        CTPScriptDicomTagParseError
            If this tag cannot be resolved into canonical form

        """

        # try the simplest case: tag string is already canonical
        tag_string = self.tag_string
        if self.is_flat_dicom_tag(tag_string):
            return

        # if this did not work, try parsing it as a dicom tag name like 'Modality'
        original = self.tag_string
        canonical = self.resolve_dicom_tag_name(original)
        if self.is_flat_dicom_tag(canonical):
            # This is a recognized tag name like 'PatientID'. Change
            # tag_string to canonical form,
            # but save name for readable printing later
            self.tag_name = original
            self.tag_string = canonical
            return

        # if that did not work either, try heaver things. Try to substitute
        # private tag creators the CTP way
        tag_string = self.resolve_private_creator_tags(
            tag_string=tag_string, context=context
        )
        if self.is_flat_dicom_tag(tag_string):
            self.tag_string = tag_string
            return

        raise CTPScriptDicomTagParseError(
            f"Could not parse tag '{tag_string}' into canonical form '12341234'"
        )

    def as_pydicom_tag(self):
        """Cast this tag to a pydicom BaseTag

        Returns
        -------
        pydicom.BaseTag

        Raises
        ------
        CTPScriptDicomTagParseError
            If casting fails

        """
        if not self.is_flat_dicom_tag(self.tag_string):
            msg = (
                f"Could not cast {self} to pydicom tag. Was this tag resolved?"
            )
            raise CTPScriptDicomTagParseError(msg)

        return BaseTag(self.hex_to_int(self.tag_string))

    @staticmethod
    def resolve_private_creator_tags(
        tag_string, context: CTPConfigScriptContext
    ):
        """Try to resolve a tag like '0075[ANONYMIZER]81' into '00751081'

        Parameters
        ----------
        tag_string: str
            string like '0075[ANONYMIZER]81'
        context: CTPConfigScriptContext
            The context to use to resolve this tag

        Returns
        -------
        str
            hex representation of tag, like '00801010' if possible, or
            unresolved if resolution was not possible


        """

        # try to replace private creator tag values. get the dicom tag group:
        result = re.match(r"(?P<dicom_group>[0-9]{4})\[", tag_string)
        if not result:
            raise CTPScriptDicomTagParseError(
                f"Could not parse tag '{tag_string}'"
            )

        dicom_group = result["dicom_group"]
        # find all private creators for the group that this tag is in

        private_creator_tags = [
            x
            for x in context.dicom_values
            if x.tag.is_private_creator and x.tag.group == int(dicom_group, 16)
        ]

        for tag in private_creator_tags:
            tag_string = tag_string.replace(
                f"[{tag.value}]", hex(tag.tag.elem)[2:]
            )

        return tag_string

    @staticmethod
    def resolve_dicom_tag_name(keyword):
        """Return DICOM tag string for this DICOM tag keyword, or None if
        tag cannot be found

        Uses pydicom internally

        Parameters
        ----------
        keyword: str
            A DICOM tag keyword like 'Modality'

        Returns
        -------
        str
            hex representation of tag, like '00801010', or original string
            if resolution failed


        """
        key_int = tag_for_keyword(keyword)
        if key_int:
            # silly way to convert int representation back to 8 digit hex
            return hex(key_int)[2:].zfill(8)

        else:
            return keyword

    @staticmethod
    def is_flat_dicom_tag(tag_string):
        """Is this tag just 8 hexadicimals, meaning this can be used as a
        DICOM tag as is?

        Returns
        -------
        True:
            if this tag can be used as a dicom tag directly
        False:
            if not, for example because it is not a tag at all or it needs
            resolution of variables
        """
        return bool(re.search("[0-9,a-f,A-F]{8}", tag_string))

    def ctp_script_string(self):
        """Try to use name like 'modality', fall back on plain string"""
        tag_string = self.tag_name
        if not tag_string:
            tag_string = self.tag_string
        if self.modifier:
            return self.modifier + ":" + tag_string
        else:
            return tag_string


class CTPExpression(CTPLinePrintable):
    """A part of a CTP rule that is true or false. Like 'tagX contains
    'foo'' or 'tagY is empty'
    """

    @staticmethod
    def get_pydicom_tag(tag):
        """Get pydicom version of this tag

        Returns
        -------
        pydicom.DataElement


        Raises
        ------
        CTPExpressionEvaluationError
            if this is not possible, for example because the tag has not
            been resolved
        """
        try:
            return tag.as_pydicom_tag()
        except CTPScriptDicomTagParseError as e:
            raise CTPExpressionEvaluationError(e) from e

    @abstractmethod
    def is_true(self, context):
        """See whether this expression evaluates to True or False

        Parameters
        ----------
        context: CTPConfigScriptContext

        Returns
        -------
        Bool
            True if this expression is true, et cetera.

        Raises
        ------
        CTPExpressionEvaluationError:
            when truth value cannot be determined

        """
        pass


class Contains(CTPExpression, Resolvable):
    """see whether tag x contains expression y"""

    def ctp_script_string(self):
        return (
            f"({self.tag.ctp_script_string()},contains,"
            f"{self.value.ctp_script_string()})"
        )

    def __init__(self, tag: CTPDicomTag, value):
        self.tag = tag
        self.value = value

    def __str__(self):
        return f"Expression: {str(self.tag)} contains {str(self.value)}"

    def is_true(self, context):
        """See which value this expression takes, given context

        Parameters
        ----------
        context: CTPConfigScriptContext
            use this context to determine truth value
        """
        self.resolve(context)
        try:
            tag_value = context.dicom_values[
                self.get_pydicom_tag(self.tag)
            ].value
            return str(self.value) in tag_value
        except KeyError:
            #  according to the CTP manual, equals is false even if the
            #  tag cannot be found at all
            return False


class Equals(CTPExpression, Resolvable):
    """see whether tag x contains expression y"""

    def __init__(self, tag: CTPDicomTag, value):
        self.tag = tag
        self.value = value

    def __str__(self):
        return f"Expression: {self.tag} equals {self.value}"

    def ctp_script_string(self):
        return (
            f"({self.tag.ctp_script_string()},equals,"
            f"{self.value.ctp_script_string()})"
        )

    def is_true(self, context):
        """See which value this expression takes, given context

        Parameters
        ----------
        context: CTPConfigScriptContext
            use this context to determine truth value
        """

        self.resolve(context)
        try:
            tag_value = context.dicom_values[
                self.get_pydicom_tag(self.tag)
            ].value
            return self.value == tag_value
        except KeyError:
            # according to the CTP manual, equals is false even if the
            # tag cannot be found at all
            return False


class Matches(CTPExpression, Resolvable):
    """see whether tag contents matches regex expression y"""

    def __init__(self, tag: CTPDicomTag, regex):
        """

        Parameters
        ----------
        tag: CTPDicomTag
            match the contents of this tag
        regex: CTPStringLiteral
            The regex string to match
        """
        self.tag = tag
        self.regex = regex

    def __str__(self):
        return f"Expression: {self.tag} matches {self.regex}"

    def ctp_script_string(self):
        return f"({self.tag.ctp_script_string()},equals,{self.regex})"

    def is_true(self, context):
        """See which value this expression takes, given context

        Parameters
        ----------
        context: CTPConfigScriptContext
            use this context to determine truth value
        """

        self.resolve(context)
        try:
            tag_value = context.dicom_values[
                self.get_pydicom_tag(self.tag)
            ].value
            return bool(re.match(self.regex, tag_value))
        except KeyError:
            # according to the CTP manual, equals is false even if the tag
            # cannot be found at all
            return False


class Exists(CTPExpression, Resolvable):
    """see whether tag x exists, disregard value"""

    def __init__(self, tag):
        self.tag = tag

    def __str__(self):
        return f"Expression: {self.tag} exists"

    def ctp_script_string(self):
        return f"({self.tag.ctp_script_string()},exists)"

    def is_true(self, context):
        """See which value this expression takes, given context

        Parameters
        ----------
        context: CTPConfigScriptContext
            use this context to determine truth value

        Raises
        ------
        CTPExpressionEvaluationError
            when truth value cannot be determined
        """
        self.resolve(context)
        try:
            _ = context.dicom_values[self.get_pydicom_tag(self.tag)].value
            return True
        except KeyError:
            return False


class IsBlank(CTPExpression, Resolvable):
    """From CTP: The isblank conditional statement executes the true clause
    if the named element is missing from the object or appears with a zero
    length or with a non-zero length and contains only blank characters;
    otherwise, it executes the false clause.
    """

    def __init__(self, tag: CTPDicomTag):
        self.tag = tag

    def __str__(self):
        return f"Expression: {self.tag} is blank"

    def ctp_script_string(self):
        return f"({self.tag.ctp_script_string()},isblank)"

    def is_true(self, context):
        """See which value this expression takes, given context

        Parameters
        ----------
        context: CTPConfigScriptContext
            use this context to determine truth value
        """
        self.resolve(context)
        try:
            value = context.dicom_values[self.get_pydicom_tag(self.tag)].value
            return value == ""
        except KeyError:
            # non existent tags are still considered blank
            return True
        return False


class CTPVariableElement(Resolvable, CTPLinePrintable):
    """Example: @DATEINC"""

    def __init__(self, name, value=None):
        self.name = name
        self.value = value

    def __str__(self):
        return f"Variable @{self.name} (value: {str(self.value)})"

    def ctp_script_string(self):
        if self.value:
            return self.value
        else:
            return f"@{self.name}"

    def resolve(self, context: CTPConfigScriptContext):
        """If this variable is defined as a parameter, take that value"""
        try:
            parameter_dict = {x.name: x.value for x in context.parameters}
        except TypeError:
            pass
        if self.name in parameter_dict.keys():
            self.value = parameter_dict[self.name]
