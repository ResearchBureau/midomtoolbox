"""Methods to say interesting things about a CTP DICOM filter pipeline; a number of dicom filter scripts that are
run in succession
"""

import textwrap

from datetime import datetime
from pathlib import Path

from pydicom import Dataset
from typing import List

from midomtoolbox.ctp.config_script import (
    CTPConfigScript,
    CTPDicomTagAction,
    CTPTraceableTagAction,
)
from midomtoolbox.ctp.elements import CTPConfigScriptContext


class PipelineContext:
    """The dicom tags that are supposed to be in the file that is being anonymized. These tags influence the
    way that the pipeline works
    """

    def __init__(self, dicom_elements: Dataset, description="Unspecified"):
        """

        Parameters
        ----------
        dicom_elements: :obj:`pydicom.Dataset`
            Collection of DICOM elements
        description: str
            Verbose description of this context. Something like 'Standard MR file in project wetenschap-algemeen'
        """
        self.dicom_elements = dicom_elements
        self.description = description


class PipelineSummary:
    def __init__(
        self, all_actions: List[CTPTraceableTagAction], directives_per_stage
    ):
        """Summary information about what a pipeline does

        Parameters
        ----------
        all_actions: List[CTPDicomTagAction]
            Collection of all actions done on specific DICOM tags in this pipeline
        directives_per_stage: Dict(stage_name: List[CTPTraceableTagAction])
            For each stage that has any directives, a list of those directives
        """
        self.all_actions = all_actions
        self.directives_per_stage = directives_per_stage

    def to_string(self):
        """Make this summary into a string"""

        # list of all directives per stage, like 'remove all curves'.
        directives_strings = []
        for stage_name, directives in self.directives_per_stage.items():
            directives = f"{stage_name}:\n" + "\n".join(
                ["  * " + x.text for x in directives]
            )
            directives_strings.append(directives)
        directives_string = "\n".join(directives_strings)

        # Find tag actions that appear multiple times.
        all_tag_codes = [x.tag_code for x in self.all_actions]
        duplicate_tag_codes = [
            x for x in all_tag_codes if all_tag_codes.count(x) > 1
        ]
        duplicate_actions = [
            x for x in self.all_actions if x.tag_code in duplicate_tag_codes
        ]

        # Print all actions. For actions that appear multiple times, print the script they come from
        # So it is easier to see for a human reader whether there is a problem in the scripts
        action_strings = []
        for action in self.all_actions:
            rule_string = action.rule.ctp_script_string()
            tag_code = f"({action.tag_code[0:4]},{action.tag_code[4:]})"  # render as '(xxxx,xxxx)'
            action_string = f"{tag_code} - {action.tag_name} : {rule_string}"
            if action in duplicate_actions:
                action_string = action_string + f" ({action.parent_script})"
            action_strings.append(action_string)
        all_actions_string = "\n".join(action_strings)

        output = (
            f"Directives per stage:\n"
            f"---------------------\n"
            f"{directives_string}\n"
            f"\n"
            f"All DICOM tag actions:\n"
            f"----------------------\n"
            f"{all_actions_string}\n"
        )

        return output


class CTPPipeline:
    def __init__(self, stages: List[CTPConfigScript], name="CTP_pipeline"):
        """A list CTP DICOM filters that are applied successively

        Parameters
        ----------
        stages: List[CTPConfigScript]
            Ordered list of the script underlying each stage.
        name: str
            Short name for this pipeline
        """
        self.stages = stages
        self.name = name

    def resolve(self, context: PipelineContext):
        """Answer the question 'given this context, what will happen to a dicom
        file anonymized by this pipeline?'

        Parameters
        ----------
        context: PipelineContext
            context with which to resolve this pipeline

        Notes
        -----
        It is possible in principle to set a dicom tag in stage 1 of a pipeline,
        and using the value of that tag to decide on an action in stage 2.
        This is powerful, but also unwieldy and unneeded. This function does not
        implement checking for this. So just don't use those constructions.
        Implementing a simulation of this behaviour is similar to actually
        re-implementing CTP in python. A nice project but a bit beyond scope
        currently.
        """

        resolved_stages = []
        for stage in self.stages:
            # Each stage uses the same input dicom elements, but its own parameters
            stage_context = CTPConfigScriptContext(
                dicom_values=context.dicom_elements,
                parameters=stage.parameters,
            )
            resolved_stages.append(stage.resolve(context=stage_context))

        return ResolvedCTPPipeline(stages=resolved_stages, context=context)

    def summarize(self):
        """Collect summary data for all this pipeline does

        This will collect all DICOM tags for which there is an action (like 1010801e: @keep()), and give a summary of
        the directives given in this pipeline.

        Returns
        -------
        PipelineSummary
            A summary of what this pipeline does

        """
        # Collect all actions done on specific tags
        all_actions = []
        for stage in self.stages:
            for action in stage.dicom_tag_actions:
                all_actions.append(
                    CTPTraceableTagAction(
                        tag_code=action.tag_code,
                        tag_name=action.tag_name,
                        rule=action.rule,
                        element=action.element,
                        parent_script=stage,
                    )
                )
        all_actions = sorted(all_actions)

        # Collect directives, if present. No more crazy-ass list comprehensions
        directives_per_stage = {}
        for stage in self.stages:
            stage_name = stage.name
            directives = stage.directives
            if directives:
                directives_per_stage[stage_name] = directives

        return PipelineSummary(
            all_actions=all_actions, directives_per_stage=directives_per_stage
        )

    def generate_summary_string(self):
        """Print an overview of all the actions and directives in all pipelines

        Return
        ------
        str

        """
        summary = self.summarize()
        output = (
            f"Summary of {len(self.stages)}-stage CTP DICOM filter pipeline:\n"
            f"\n"
            f"{summary.to_string()}"
        )

        return output


class ResolvedCTPPipeline(CTPPipeline):
    """A CTP pipeline in which each stage has been simplified as far as possible given a certain context"""

    def __init__(
        self, stages: List[CTPConfigScript], context: PipelineContext
    ):
        """

        Parameters
        ----------
        stages: List[CTPConfigScript]
            Ordered list of the script underlying each stage.
        context: PipelineContext
            context with which all these stage were resolved
        """
        super().__init__(stages=stages)
        self.context = context

    def generate_summary_string(self):
        """Print an overview of all the actions and directives in all pipelines

        Return
        ------
        str

        """
        context_string = (
            self.context.description
            + "\n"
            + "\n".join([str(x) for x in self.context.dicom_elements])
        )
        summary = self.summarize()
        output = textwrap.dedent(
            f"Summary of {len(self.stages)}-stage CTP DICOM filter pipeline\n"
            f"given the following DICOM values are used as input:\n"
            f"\n"
            f"Input context:\n"
            f"--------------\n"
            f"{context_string}\n"
            f"\n"
            f"{summary.to_string()}"
        )

        return output

    def generate_CTP_script_summary_dir(self, path: Path):
        """Generate a single CTP anonymizer script that summarizes this pipeline.

        For sending to external centers that want to have anonymization similar to ours but cannot re-create the
        entire pipeline because of expertise/time constraints.

        Parameters
        ----------
        path: Path
            write files to this folder


        """
        context_string = (
            self.context.description
            + "\n"
            + "\n".join(
                ["        " + str(x) for x in self.context.dicom_elements]
            )
        )
        stages_string = "\n".join(["        " + str(x) for x in self.stages])
        description = textwrap.dedent(
            f"""\
        Summary of CTP pipeline {self.name}
        Generated on {str(datetime.now())}
        
        Original pipeline was {len(self.stages)} stages:
        {stages_string}
        
        context used to simplify those stages:
        {context_string}
        """
        )

        summary = self.summarize()
        summary.all_actions.sort()
        summary_string = [x.ctp_script_string() for x in summary.all_actions]

        # each stage can have directives. Collect all and remove duplicates
        stages = list(summary.directives_per_stage.values())
        all_directives = []  # type: ignore [var-annotated]
        for stage in stages:
            all_directives = all_directives + stage
        unique_directives = list(set(all_directives))

        # now write all data to separate files
        path.mkdir(parents=True, exist_ok=True)
        with open(path / "readme.txt", "w") as f:
            f.write(description)

        with open(path / "Companyumc_ANON_summary.script", "w") as f:
            f.write("\n".join(summary_string))
            f.write(
                "\n".join([x.ctp_script_string() for x in unique_directives])
            )

        print(f"Written to '{str(path)}'")
