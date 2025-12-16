"""
Enumerations for the application
"""

from enum import Enum

class PipelineMode(str, Enum):
     """Pipeline execution modes"""
     EXTRACTIVE = "extractive"
     SEMANTIC = "semantic"
     ABSTRACTIVE = "abstractive"

class SectionType(str, Enum):
      """Known section types in support tickets"""
      SUMMARY = "summary"
      DESCRIPTION = "description"
      STEPS_TO_REPRODUCE = "steps_to_reproduce"
      EXPECTED_RESULT = "expected_result"
      ACTUAL_RESULT = "actual_result"
      RESOLUTION = "resolution"
      WORKAROUND = "workaround"
      ROOT_CAUSE = "root_cause"
      IMPACT = "impact"
      PRIORITY = "priority"
      BODY = "body"
      UNKNOWN = "unknown"