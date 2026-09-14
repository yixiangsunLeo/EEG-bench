# docs/papers/

Reference papers (PDFs gitignored; keep the list here).

| file | citation | why |
|:---|:---|:---|
| `2601.17883v3_EEG-FM-Compass.pdf` | Liu D, Chen Y, Chen Z, et al. EEG-FM-Compass: Progress, Benchmarking, and Future Directions for EEG Foundation Models. *Natl Sci Rev* 2026. arXiv:2601.17883v3. Code: https://github.com/Dingkun0817/EEG-FM-Benchmark | The benchmark we reproduce (Table 2, §3.2–3.4, Table 4 input specs, Table 14 datasets, §2 channel-unification taxonomy, §4.3 EA) |

Text extraction for grep: `pip install --user pypdf` then dump pages with `pypdf.PdfReader` to `/tmp` (the PDF has
88 pages; the benchmark section is pages 14–25, supplementary tables from page 27).
