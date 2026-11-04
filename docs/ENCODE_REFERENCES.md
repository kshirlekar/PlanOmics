# ENCODE Standards: What We Use and How

ENCODE data standards were written for producing **reference datasets** (QC floor, replicate concordance), not for powering **differential** experiments. We therefore use them in two ways:

1. **As QC floors** — minimum depth, read length, and quality metrics a library should meet.
2. **As provenance** — every rule citing ENCODE links to the standards page and states the version (ENCODE4 unless noted).

Where our team's recommendation differs (e.g. ≥3 replicates for differential expression vs ENCODE's ≥2), the rule says so explicitly and gives the reason.

Machine-readable values live in `knowledge/common/encode_standards.yaml`. Re-check these pages at each rulebook release.

## Bulk RNA-seq (ENCODE4, updated May 2021)
Source: https://www.encodeproject.org/data-standards/rna-seq/long-rnas/

- Bulk RNA-seq = libraries with average insert > 200 bases; ≥2 replicates.
- **30 million aligned reads per replicate** (older projects targeted 20M).
- Replicate concordance (gene-level Spearman): **>0.9 isogenic, >0.8 anisogenic**.
- Spike-ins: ENCODE standardizes on **Ambion (ERCC) Mix 1 at ~2% of final mapped reads**.
- shRNA/siRNA knockdown and CRISPR-edit RNA-seq: **10 million aligned reads per replicate**, with a matched control experiment.
- Quantification annotated to GENCODE (V29 human / M21 mouse at time of writing).

**Our deviations:** ≥3 biological replicates for DE (ENCODE minimum of 2 is for reproducibility, not power). Spike-ins recommended only when justified (global transcriptional change, absolute quantification), not by default.

## ATAC-seq (ENCODE4)
Source: https://www.encodeproject.org/atac-seq/

- Read length ≥45 bp before trimming; library insert size range must be recorded.
- **25M non-duplicate, non-mitochondrial aligned reads per replicate (SE) or 50M reads PE = 25M fragments.**
- TSS enrichment (GRCh38 RefSeq): <5 concerning, 5–7 acceptable, >7 ideal (hg19: <6, 6–10, >10).
- FRiP >0.3 ideal; >0.2 acceptable.
- Library complexity (NRF, PBC1, PBC2) reported.

## Histone ChIP-seq (ENCODE4) — reference for CUT&RUN/CUT&Tag
Source: https://www.encodeproject.org/chip-seq/histone-encode4/

- ≥2 biological replicates; antibodies characterized per ENCODE antibody standards.
- Narrow marks (e.g. H3K4me3, H3K27ac): **20M usable fragments per replicate**.
- Broad marks (e.g. H3K27me3, H3K36me3): **45M usable fragments** (35M acceptable). H3K9me3 is a special case (repeats).
- Matched input/control with the same run type, read length and replicate structure.

**Important:** ENCODE has **no dedicated CUT&RUN/CUT&Tag standard**. These assays have much lower background and need far fewer reads than ChIP-seq. Our CUT&RUN/Tag module will use team rules and published method papers, citing ENCODE ChIP standards only for antibody validation and replicate structure. Rules will be labeled `source: team` or `source: literature`, not `encode`.

## scRNA-seq
Source: https://www.encodeproject.org/data-standards/encode4-single-cell-rna/

ENCODE documents its single-cell pipeline (10x and Parse Split-seq) but does not set numeric design standards (cells per sample, reads per cell). The scRNA module will use platform vendor guidance and literature, labeled accordingly.
