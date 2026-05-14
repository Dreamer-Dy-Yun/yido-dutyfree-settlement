# LLM/prompt

This folder stores prompt text files used by OCR/LLM setup and experiments.

## Files

| Path | Responsibility |
| --- | --- |
| `prompt_yido.txt` | Main YIDO prompt text. |
| `prompt_yido poc(max-data).txt` | POC prompt variant with expanded data. |
| `prompt_yido(eng, 문제있음).txt` | English/problematic prompt variant retained for reference. |

## Boundary Notes

- Runtime prompt selection should come from DB `Prompt` records when using the active OCR service.
- Prompt edits can change OCR output contracts; update parser expectations when needed.
