from pydantic import BaseModel, Field, field_validator
from typing import List, Optional

# ==========================================
# SYSTEM PROMPTS
# ==========================================

RELEVANCE_SYSTEM_PROMPT = """You are YouParts Relevance Analyzer.
    Your task is to evaluate video titles and descriptions from DIY gaming hardware build series.
    Analyze if the video contains parts or build instructions relevant to the user's specific target build:
        - Target Build: DIY Force Feedback (FFB) Steering Wheel, Clutch Pedal Assembly, and BeamNG.drive integration.

        Rules:
            1. Output MUST strictly follow this exact JSON key structure:
                {
                    "relevance_score": 0.85,
                    "is_relevant": true,
                    "has_clutch_content": true,
                    "has_ffb_content": true,
                    "beamng_compatible": true,
                    "key_components_mentioned": ["Arduino", "GT2 Belt"],
                    "reasoning": "Covers FFB steering wheel base and clutch pedal wiring."
                }
                2. Do NOT invent parts not mentioned in the text.
                3. Mark videos about handbrakes only or non-FFB wheels as lower relevance (< 0.5) unless they share clutch/wiring hardware.
                """

EXTRACTION_SYSTEM_PROMPT = """You are YouParts Hallucination-Guarded Extraction Engine.
Your job is to parse YouTube video descriptions and transcript overlays from DIY build videos into a verified Bill of Materials (BOM).

STRICT ANTI-HALLUCINATION RULES:
1. ONLY extract physical parts, hardware, tools, components, and links explicitly stated in the text.
2. DO NOT infer or guess unstated dimensions.
3. Output MUST strictly follow this exact JSON key structure:
{
    "required_parts": [
        {
            "part_name": "Arduino Pro Micro",
            "category": "Electronics",
            "quantity": "1",
            "specs_and_dimensions": "5V 16MHz ATmega32U4",
            "logic_gap_warning": null
        }
    ],
    "optional_parts": [],
    "external_resources": [
        {
            "resource_type": "Google Drive Folder",
            "title": "3D STL Pedal Files",
            "url": "https://drive.google.com/..."
        }
    ],
    "overall_logic_gaps": [
        {
            "description": "Bolt length missing for motor mount",
            "approx_timestamp_seconds": 142
        }
    ]
}
"""

# ==========================================
# PHASE 1: RELEVANCE SCREENING MODELS
# ==========================================


class VideoRelevanceAnalysis(BaseModel):
    video_id: str
    title: str
    relevance_score: float = Field(
        default=0.5,
        description="Relevance from 0.0 to 1.0 for DIY force-feedback wheel, clutch pedal, or BeamNG setup",
    )
    is_relevant: bool = Field(default=False, description="True if score >= 0.65")
    has_clutch_content: bool = Field(
        default=False, description="Does this video cover clutch design/wiring?"
    )
    has_ffb_content: bool = Field(
        default=False, description="Does this video cover force feedback base/motors?"
    )
    beamng_compatible: bool = Field(
        default=False, description="Is this applicable to BeamNG.drive setup?"
    )
    key_components_mentioned: List[str] = Field(default_factory=list)
    reasoning: str = Field(
        default="Analysis complete.",
        description="Brief 1-sentence reason for relevance score",
    )


# ==========================================
# PHASE 2: GROUNDED BOM EXTRACTION MODELS
# ==========================================


class BOMItem(BaseModel):
    part_name: str = Field(
        default="Unknown Component",
        description="Name of the physical part or component",
    )
    category: str = Field(
        default="Hardware",
        description="Category: Electronics, Mechanical, Hardware, 3D Print / CAD, or Tools",
    )
    quantity: str = Field(
        default="1", description="Quantity required (e.g., '1', '2 units', '12 inches')"
    )
    specs_and_dimensions: Optional[str] = Field(
        default=None,
        description="Explicitly stated specs (e.g., '60T GT2 Pulley, 8mm bore'). Do NOT guess if omitted!",
    )
    alternative_parts: List[str] = Field(
        default_factory=list,
        description="Alternative parts or sizing options mentioned in text",
    )
    logic_gap_warning: Optional[str] = Field(
        default=None,
        description="Populate if crucial size/spec is missing. E.g., 'Bolt length missing. Check video description link for CAD files.'",
    )
    bought: bool = Field(
        default=False, description="Whether the component has been acquired"
    )
    merged_from: List[str] = Field(
        default_factory=list,
        description="Audit trail of component names merged into this item",
    )


class ExternalResource(BaseModel):
    resource_type: str = Field(
        default="External Resource",
        description="Type: '3D Model / STL', 'Wiring Diagram', 'Assembly Guide', 'Parts Purchase Link', 'Firmware / Code'",
    )
    title: str = Field(
        default="Resource Link", description="Short description of the resource link"
    )
    url: str = Field(description="Full target URL extracted from description or text")


class LogicGap(BaseModel):
    description: str = Field(description="Details of missing specs or instructions")
    approx_timestamp_seconds: Optional[int] = Field(
        default=None,
        description="Approximate timestamp in seconds where the gap occurs if stated/inferrable, else null.",
    )


class VideoBOMExtraction(BaseModel):
    video_id: str
    video_title: str
    video_url: str
    required_parts: List[BOMItem] = Field(default_factory=list)
    optional_parts: List[BOMItem] = Field(default_factory=list)
    external_resources: List[ExternalResource] = Field(default_factory=list)
    overall_logic_gaps: List[LogicGap] = Field(
        default_factory=list,
        description="List of any missing details the user must inspect manually",
    )

    @field_validator("overall_logic_gaps", mode="before")
    @classmethod
    def coerce_logic_gaps(cls, value):
        """Coerces legacy string gaps / raw dicts into LogicGap instances.

        The LLM sometimes emits strings or bare dicts for overall_logic_gaps;
        normalizing here keeps extraction resilient to key improvisation.
        """
        if value is None:
            return []
        coerced = []
        for gap in value:
            if isinstance(gap, LogicGap):
                coerced.append(gap)
            elif isinstance(gap, dict):
                coerced.append(LogicGap(**gap))
            else:
                coerced.append(LogicGap(description=str(gap)))
        return coerced
