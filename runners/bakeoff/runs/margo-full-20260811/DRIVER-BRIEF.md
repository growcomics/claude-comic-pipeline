# margo-full generation driver brief (mechanical — follow exactly)

RUN DIR (always cd here, absolute):
`/Users/mattmenashe/Documents/claude-comic-pipeline/runners/bakeoff/runs/margo-full-20260811`

You will be given a list of BEAT IDs. Process them ONE AT A TIME, in order.

## Step 0 — load the Higgsfield tools once
```
ToolSearch query: select:mcp__c26fa20c-5548-4848-81c2-e089d37673c6__generate_image,mcp__c26fa20c-5548-4848-81c2-e089d37673c6__jobs_wait
```

## Step 1 — read the beat plan
`plan/<beat>.json` holds: `prompt` (use VERBATIM — never edit, shorten, or rewrite it),
`aspect_ratio`, `medias` (list of {value, role}), `variants` (8 or 12).

Read it with the Read tool. Do NOT paraphrase the prompt.

## Step 2 — submit
Call `generate_image` with `params`:
```
{ "model": "nano_banana_2_lite",
  "aspect_ratio": <aspect_ratio from plan>,
  "count": 4,
  "use_unlim": false,
  "prompt": <prompt VERBATIM>,
  "medias": <medias from plan> }
```
Repeat this call **2 times** if variants==8, **3 times** if variants==12.
Each call costs 1 credit and returns 4 job ids in `results[].id`.
Keep the job ids grouped BY CALL — one group per call.

If a call errors with a rate limit (429) or "too many", back off and retry the SAME call
(up to 5 tries). To back off, use the Bash tool with
`python3 -c "import time; time.sleep(40)"` — the Bash tool blocks a foreground `sleep`,
but this form works. **Never end your turn to wait** for a backoff or a poll.
If a call is refused by a content filter, retry it once unchanged; if it fails again,
note it and move on — do NOT rewrite the prompt.

## Step 3 — poll
Call `jobs_wait` with all the job ids from that beat (max 12 per call, index them 1..N).
If `all_terminal` is false, wait `poll_after_seconds` (use the Bash tool: no foreground
sleep >60s) and call `jobs_wait` again. Up to 8 polls. Record each job's `result_url`.

## Step 4 — record + download
For EACH submit group (calls in step 2), run in the run dir:
```
python3 drive.py record <beat> <groupnum> <jobid1> <jobid2> <jobid3> <jobid4>
python3 drive.py fetchroll <beat> "<result_url of any COMPLETED job in that group>"
```
`fetchroll` derives sibling URLs from the shared timestamp prefix, so it only works
within one submit group. Run it once per group. If it reports MISS for a job that was
completed, fall back to the explicit form for that job:
```
python3 drive.py fetch <beat> <jobid> "<result_url>"
```

## Step 5 — contact sheet
```
python3 drive.py sheet <beat>
```
Confirm `variants/<beat>/` has at least 6 files. If it has fewer than 6, submit ONE more
`count:4` call for that beat and repeat steps 3-4.

## Step 6 — report line
After each beat print one line:
`<beat>: files=<N> jobs=<ids comma-separated>`

## Hard rules
- NEVER edit the prompt text. It is the composed, audited prompt.
- NEVER call `drive.py winner` — banking is not your job.
- NEVER read/view the generated images. You are a submit/download driver only.
- Keep your prose to a minimum; the report is a list of the step-6 lines.
- Do not touch git.
