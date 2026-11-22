# Free GPUs (batch jobs)

Free GPUs run batch jobs for VASH: a model over a list of prompts, the answers saved (`vash gpu`). None of them
serves a model as a live endpoint: their free tiers are sessions with time limits, and their terms do not allow
using them as remote servers, so the always-on work stays on the VM and the free model APIs (the gateway).

| Provider | Free GPU (about; checked in activity 3.3) | VASH starts it | Status |
|---|---|---|---|
| Kaggle | about 30 GPU hours a week (T4 x2), sessions up to 12 h | yes: official client `kaggle` 2.2.5 (Apache-2.0), quota read from Kaggle | adapter `gpu/kaggle` |
| Lightning AI | monthly free credits | yes, through its SDK (terms to check) | next |
| Google Colab | T4 when available | no: its free tier does not allow remote or unattended use | the owner, by hand |
| Amazon SageMaker Studio Lab | about 4 GPU hours a day | no API | the owner, by hand |

Hosted free model APIs on GPUs (NVIDIA NIM, Hugging Face, Cloudflare Workers AI, SambaNova, ...) are providers of
the model gateway instead (`catalog/llm/gateway.json`).

A job's prompts leave the VM, so they hold no client data (rule R2): `vash gpu run` needs `--no-client-data`
until the gatekeeper masks data.
