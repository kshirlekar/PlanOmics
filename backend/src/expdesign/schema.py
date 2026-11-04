"""Design-state schema: the single source of truth for an experiment design.

Every field is optional so a design can be filled in progressively during the
interview. The rules engine reports which required fields are still missing.
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class Project(BaseModel):
    title: Optional[str] = None
    pi: Optional[str] = None
    funding_context: Optional[Literal["grant", "pilot", "preliminary_data", "other"]] = None
    irb_status: Optional[str] = None
    budget_ceiling_usd: Optional[float] = None


class Question(BaseModel):
    goal: Optional[Literal["gene_level_de", "isoform", "splicing", "fusion", "lncRNA", "other"]] = None
    expected_global_transcription_change: Optional[bool] = None
    description: Optional[str] = None


class Sample(BaseModel):
    organism: Optional[Literal["human", "mouse", "rat", "zebrafish", "other"]] = None
    source: Optional[Literal[
        "cell_line", "patient_tissue", "animal_tissue", "whole_blood", "pbmc",
        "sorted_cells", "organoid", "pdx", "other"]] = None
    preservation: Optional[Literal["fresh", "fresh_frozen", "ffpe", "rnalater", "other"]] = None
    collection_tube: Optional[Literal["paxgene", "tempus", "edta", "other"]] = None
    rin: Optional[float] = None
    dv200: Optional[float] = None
    input_ng: Optional[float] = None
    passage_range: Optional[str] = None
    str_authenticated: Optional[bool] = None
    mycoplasma_tested: Optional[bool] = None
    cell_counts_available: Optional[bool] = None


class Design(BaseModel):
    factors: dict[str, list[str]] = Field(default_factory=dict)  # e.g. {"treatment": ["DMSO","drugX"]}
    biological_replicates_per_group: Optional[int] = None
    paired: Optional[bool] = None
    perturbation_type: Optional[str] = None
    matched_nontargeting_control: Optional[bool] = None
    batch_confounded_with_condition: Optional[bool] = None


class Library(BaseModel):
    prep: Optional[Literal["polyA", "rRNA_depletion", "three_prime_tag", "low_input_full_length"]] = None
    stranded: Optional[bool] = True
    globin_depletion: Optional[bool] = None
    spike_in: Optional[str] = None
    umi: Optional[bool] = None


class Sequencing(BaseModel):
    target_reads_per_sample: Optional[int] = None
    paired_end: Optional[bool] = None
    read_length: Optional[int] = None


class Analysis(BaseModel):
    host_read_removal: Optional[bool] = None
    model_formula: Optional[str] = None


class DesignState(BaseModel):
    assay: Literal["bulk_rnaseq", "atacseq", "cutrun", "cuttag", "scrnaseq"] = "bulk_rnaseq"
    project: Project = Field(default_factory=Project)
    question: Question = Field(default_factory=Question)
    sample: Sample = Field(default_factory=Sample)
    design: Design = Field(default_factory=Design)
    library: Library = Field(default_factory=Library)
    sequencing: Sequencing = Field(default_factory=Sequencing)
    analysis: Analysis = Field(default_factory=Analysis)

    def n_groups(self) -> int:
        n = 1
        for levels in self.design.factors.values():
            n *= max(len(levels), 1)
        return n

    def n_samples(self) -> Optional[int]:
        reps = self.design.biological_replicates_per_group
        return self.n_groups() * reps if reps else None
