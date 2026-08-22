#!/usr/bin/env python3
"""
Build forum.hal0.dev's structured post types out of core form templates.

Three things, in order:
  1. tag groups — the structured dimensions. tag-chooser fields bind to these,
     which is what makes the answers real tags: filterable, browsable at
     /tags, and queryable from Data Explorer. Everything else a form template
     collects ends up as prose in the post body.
  2. form templates — one per post type.
  3. category assignment — which composer opens where.

Idempotent: matches by name, updates in place, creates only what is missing.

Why this lives in git
---------------------
Form templates, tag groups and their category assignments are stored in the
Discourse database and nowhere else. There is no export, and nothing in the
launcher's rebuild path recreates them. Left alone, the forum's entire
content model would be a thing that exists only in one Postgres instance and
in whoever's memory. This script is the source of truth; the database is a
deployment of it.

Uses the same credentials as push-color-schemes.py — see that script's
--help. Discourse rate-limits admin writes fairly aggressively, so this
sleeps between calls and backs off on 429; a full run takes a couple of
minutes.

    python3 scripts/push-content-model.py

Deliberately NOT handled here: deleting tags, tag groups or templates that
this file no longer declares. Removing a tag that topics already carry is
destructive and belongs in a human's hands, not in a sync script.
"""
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ENV_FILE = "/srv/secrets/discourse-api.env"

env = {}
for line in open(ENV_FILE):
    line = line.strip()
    if line and not line.startswith("#"):
        k, _, v = line.partition("=")
        env[k] = v

BASE = env["DISCOURSE_URL"].rstrip("/")
HEADERS = {
    "Api-Key": env["DISCOURSE_API_KEY"],
    "Api-Username": env.get("DISCOURSE_API_USERNAME", "system"),
    "Accept": "application/json",
}


def call(method, path, payload=None, form=None, retries=4):
    url = BASE + path
    headers = dict(HEADERS)
    body = None
    if payload is not None:
        body = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"
    elif form is not None:
        body = urllib.parse.urlencode(form, doseq=True).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    for attempt in range(retries):
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                raw = resp.read().decode()
                return json.loads(raw) if raw.strip() else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode()
            if exc.code == 429 and attempt < retries - 1:
                wait = 20 * (attempt + 1)
                print(f"    rate limited, waiting {wait}s")
                time.sleep(wait)
                continue
            sys.exit(f"{method} {path} -> HTTP {exc.code}\n{detail[:500]}")


# ---------------------------------------------------------------------------
# 1. Tag groups
# ---------------------------------------------------------------------------
TAG_GROUPS = {
    "Intent": ["chat", "moe", "coding", "agent", "vision", "draft", "embedding"],
    "Lane": ["rocm", "vulkan-radv", "cpu", "npu"],
    "Model Family": ["llama", "qwen", "mistral", "gemma", "deepseek",
                     "gpt-oss", "glm", "phi", "other-model"],
    "Workload": ["decode-tg", "prefill-pp", "mixed"],
    "Platform": ["strix-halo", "npu-xdna", "gorgon-halo"],
    "Quant": ["fp16", "q8-0", "q6-k", "q5-k-m", "q4-k-m",
              "rocmfp4", "mxfp4", "awq", "other-quant"],
}


def sync_tag_groups():
    existing = {g["name"]: g for g in call("GET", "/tag_groups.json")["tag_groups"]}
    for name, tags in TAG_GROUPS.items():
        payload = {"tag_group": {"name": name, "tag_names": tags}}
        if name in existing:
            call("PUT", f"/tag_groups/{existing[name]['id']}.json", payload)
            print(f"  updated  tag group {name!r} ({len(tags)} tags)")
        else:
            call("POST", "/tag_groups.json", payload)
            print(f"  created  tag group {name!r} ({len(tags)} tags)")
        time.sleep(2)


# ---------------------------------------------------------------------------
# 2. Form templates
#
# Field ids must be unique within a template and must avoid Discourse's
# reserved keywords (title, body, category, category_id, tags).
# ---------------------------------------------------------------------------
RUNNER_PROFILE = """\
- type: input
  id: profile-slug
  attributes:
    label: "Profile slug"
    description: "Lowercase, hyphenated. Matches the slug in hal0-profiles if you have submitted it there."
    placeholder: "qwen3-30b-coding-rocm"
  validations:
    required: true
- type: tag-chooser
  id: intent
  tag_group: "Intent"
  attributes:
    label: "Intent"
    description: "What this profile is tuned to do."
    multiple: false
  validations:
    required: true
- type: tag-chooser
  id: lane
  tag_group: "Lane"
  attributes:
    label: "Lane"
    description: "Backend this profile runs on."
    multiple: false
  validations:
    required: true
- type: tag-chooser
  id: model-family
  tag_group: "Model Family"
  attributes:
    label: "Model family"
    multiple: true
  validations:
    required: true
- type: tag-chooser
  id: quant
  tag_group: "Quant"
  attributes:
    label: "Quantisation"
    multiple: false
  validations:
    required: false
- type: textarea
  id: flag-string
  attributes:
    label: "Flag string"
    description: "The llama.cpp / runtime arguments, exactly as you pass them."
    placeholder: "-ngl 99 -c 32768 --parallel 4 ..."
  validations:
    required: true
- type: textarea
  id: toml-config
  attributes:
    label: "Profile TOML"
    description: "Optional. Paste the hal0 profile TOML if you have one."
  validations:
    required: false
- type: composer
  id: rationale
  attributes:
    label: "Why this configuration"
    description: "What you tried, what moved the needle, what did not. This is the part other people learn from."
  validations:
    required: true
"""

BENCHMARK_RUN = """\
- type: tag-chooser
  id: model-family
  tag_group: "Model Family"
  attributes:
    label: "Model family"
    multiple: false
  validations:
    required: true
- type: input
  id: model-id
  attributes:
    label: "Model"
    description: "Full model identifier, including size and quant."
    placeholder: "Qwen3-30B-A3B-Instruct ROCmFP4"
  validations:
    required: true
- type: tag-chooser
  id: lane
  tag_group: "Lane"
  attributes:
    label: "Lane"
    multiple: false
  validations:
    required: true
- type: tag-chooser
  id: workload
  tag_group: "Workload"
  attributes:
    label: "Workload"
    description: "Decode (token generation), prefill (prompt processing), or a mixed run."
    multiple: false
  validations:
    required: true
- type: tag-chooser
  id: quant
  tag_group: "Quant"
  attributes:
    label: "Quantisation"
    multiple: false
  validations:
    required: true
- type: input
  id: decode-tps
  attributes:
    label: "Decode (tok/s)"
    placeholder: "42.7"
  validations:
    required: false
- type: input
  id: prefill-tps
  attributes:
    label: "Prefill (tok/s)"
    placeholder: "1180"
  validations:
    required: false
- type: input
  id: ttft-p50
  attributes:
    label: "TTFT p50 (ms)"
    placeholder: "310"
  validations:
    required: false
- type: input
  id: context-depth
  attributes:
    label: "Context depth"
    description: "Tokens of context the run was measured at."
    placeholder: "8192"
  validations:
    required: false
- type: textarea
  id: methodology
  attributes:
    label: "How it was measured"
    description: "Command line, iteration count, warmup, thermal state. A number without a method is not a benchmark."
  validations:
    required: true
- type: composer
  id: observations
  attributes:
    label: "Observations"
  validations:
    required: false
"""

HARDWARE_REPORT = """\
- type: input
  id: box
  attributes:
    label: "Box"
    description: "Make and model, or a description if it is a build."
    placeholder: "Framework Desktop 128GB"
  validations:
    required: true
- type: input
  id: bios-version
  attributes:
    label: "BIOS / firmware version"
    placeholder: "3.05"
  validations:
    required: true
- type: input
  id: kernel-version
  attributes:
    label: "Kernel"
    placeholder: "6.18.2-arch1-1"
  validations:
    required: true
- type: input
  id: distro
  attributes:
    label: "Distribution"
    placeholder: "CachyOS / Ubuntu 24.04 / Fedora 42"
  validations:
    required: true
- type: input
  id: rocm-version
  attributes:
    label: "ROCm version"
    description: "Leave blank if not applicable."
    placeholder: "7.0.1"
  validations:
    required: false
- type: dropdown
  id: report-kind
  attributes:
    label: "Kind of report"
    filterable: false
  choices:
    - "Working configuration"
    - "Problem I am stuck on"
    - "Problem I solved"
    - "Measurement or observation"
  validations:
    required: true
- type: composer
  id: detail
  attributes:
    label: "Detail"
    description: "What you saw, what you expected, what you have already tried. Paste logs in a code block."
  validations:
    required: true
"""

TEMPLATES = [
    # v2 (2026-08-22): categories consolidated for launch — see the ultraplan's
    # empty-room defense. Profiles & Benchmarks (slug "profiles") carries both
    # registry templates; Hardware (slug "hardware") carries hardware reports,
    # with the platform expressed by the "Platform" tag group instead of
    # per-platform categories.
    ("hal0 · Runner profile", RUNNER_PROFILE, ["profiles"]),
    ("hal0 · Benchmark run", BENCHMARK_RUN, ["profiles"]),
    ("hal0 · Hardware report", HARDWARE_REPORT, ["hardware"]),
]


def sync_templates():
    existing = {t["name"]: t for t in
                call("GET", "/admin/customize/form-templates.json")["form_templates"]}
    assignments = {}
    for name, template, category_slugs in TEMPLATES:
        payload = {"name": name, "template": template}
        if name in existing:
            template_id = existing[name]["id"]
            call("PUT", f"/admin/customize/form-templates/{template_id}.json", payload)
            print(f"  updated  template {name!r} (id {template_id})")
        else:
            created = call("POST", "/admin/customize/form-templates.json", payload)
            template_id = created["form_template"]["id"]
            print(f"  created  template {name!r} (id {template_id})")
        for slug in category_slugs:
            assignments.setdefault(slug, []).append(template_id)
        time.sleep(2)
    return assignments


def assign_categories(assignments):
    categories = {c["slug"]: c for c in
                  call("GET", "/categories.json?include_subcategories=true")
                  ["category_list"]["categories"]}
    for slug, template_ids in assignments.items():
        cat = categories.get(slug)
        if not cat:
            print(f"  SKIP     no category {slug!r}")
            continue
        call("PUT", f"/categories/{cat['id']}.json", form={
            "name": cat["name"],
            "form_template_ids[]": template_ids,
        })
        print(f"  assigned templates {template_ids} -> /c/{slug}")
        time.sleep(3)


if __name__ == "__main__":
    print("tag groups:")
    sync_tag_groups()
    print("form templates:")
    assignments = sync_templates()
    print("category assignment:")
    assign_categories(assignments)
