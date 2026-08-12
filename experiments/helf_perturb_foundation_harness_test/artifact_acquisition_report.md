# HELF Foundation Artifact Acquisition Report

## scGPT Whole-Human Checkpoint

- Artifact id: `scgpt_whole_human_checkpoint`
- Expected path: `/home/Models/scGPT/whole_human`
- Selected blocker count in this run: `46`
- Official/primary source located: `https://github.com/bowang-lab/scGPT`
- Source note: the official scGPT README includes a pretrained model zoo and recommends the `whole-human` checkpoint, with a Google Drive download link and paired vocabulary file.
- Acquisition status: `blocked_pending_source_backed_resolver`
- Reason: the current HELF demo repo has no executable HELF resolver for downloading the Google Drive checkpoint, validating checkpoint files, validating the paired gene vocabulary, and aligning vocab/order to the HELF h5ad-derived task. The K562 acquisition source registry is not a valid HELF resolver.
- Strict-policy decision: no fallback, no proxy embedding, no random checkpoint, and no graph file substitution were used. Foundation proposals requiring this artifact were marked `requires_artifact_acquisition` and search continued to executable queued candidates.

## Next Step

Add a HELF-scoped resolver that downloads the official scGPT whole-human checkpoint folder, records URL/revision/checksums, validates required files and vocabulary, then implements a node-local encoder/head smoke contract before enabling scGPT proposals for training.
