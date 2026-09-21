PACKAGE_NAME             ?= $(PROJECT_SLUG)
SBOM_METADATA_PYTHON     ?= $(if $(wildcard $(VENV_PYTHON)),$(VENV_PYTHON),python3.11)
GIT_SHA                  ?= $(shell git -C "$(MONOREPO_ROOT)" rev-parse --short HEAD 2>/dev/null || echo unknown)
SBOM_PYPROJECT           ?= pyproject.toml
SBOM_VERSION_RESOLVER    ?=
SBOM_PYTHON_ENV          ?=
# Match this repository's simple vMAJOR.MINOR.PATCH tags and configured
# hatch-vcs guess-next-dev scheme. Dirty, absent, or unfamiliar SCM metadata
# is refused instead of being fabricated as 0.0.0.
SBOM_SNAPSHOT_PROVENANCE ?= $(MONOREPO_ROOT)/.sbom-snapshot-provenance.json
SBOM_GIT_TOPLEVEL        := $(shell git -C "$(MONOREPO_ROOT)" rev-parse --show-toplevel 2>/dev/null)
SBOM_HAS_ROOT_GIT        := $(if $(filter $(realpath $(MONOREPO_ROOT)),$(realpath $(SBOM_GIT_TOPLEVEL))),1,)
SBOM_GIT_DESCRIBE_RAW    ?= $(shell git -C "$(MONOREPO_ROOT)" describe --dirty --tags --long --match 'v[0-9]*' 2>/dev/null)
SBOM_GIT_DESCRIBE         = $(shell printf '%s\n' "$(SBOM_GIT_DESCRIBE_RAW)" | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+-[0-9]+-g[[:xdigit:]]+$$' || true)
SBOM_GIT_TAG              = $(word 1,$(subst -, ,$(SBOM_GIT_DESCRIBE)))
SBOM_GIT_DISTANCE         = $(word 2,$(subst -, ,$(SBOM_GIT_DESCRIBE)))
SBOM_TAG_COMPONENTS       = $(subst ., ,$(patsubst v%,%,$(SBOM_GIT_TAG)))
SBOM_SCM_VERSION          = $(if $(SBOM_GIT_DESCRIBE),$(if $(filter 0,$(SBOM_GIT_DISTANCE)),$(patsubst v%,%,$(SBOM_GIT_TAG)),$(word 1,$(SBOM_TAG_COMPONENTS)).$(word 2,$(SBOM_TAG_COMPONENTS)).$(shell expr $(word 3,$(SBOM_TAG_COMPONENTS)) + 1).dev$(SBOM_GIT_DISTANCE)))
SBOM_VERSION             ?= $(strip $(if $(SBOM_VERSION_RESOLVER),$(shell $(SBOM_PYTHON_ENV) $(SBOM_METADATA_PYTHON) $(SBOM_VERSION_RESOLVER) --pyproject "$(SBOM_PYPROJECT)" --package-name "$(PACKAGE_NAME)" 2>/dev/null),$(SBOM_SCM_VERSION)))
SBOM_VERSION_SAFE         = $(shell printf '%s' "$(SBOM_VERSION)" | tr ' /' '__' | tr -s '_' '_')

SBOM_DIR                 ?= $(PROJECT_ARTIFACTS_DIR)/sbom
SBOM_FORMAT              ?= cyclonedx-json
SBOM_CLI                 ?= cyclonedx
SBOM_DEV_GROUP           ?= dev
SBOM_REQUIREMENTS_WRITER ?=
SBOM_IGNORE_IDS          ?=
SBOM_IGNORE_FLAGS         = $(foreach V,$(SBOM_IGNORE_IDS),--ignore-vuln $(V))
SBOM_PROD_REQ            ?= $(SBOM_DIR)/requirements.prod.txt
SBOM_DEV_REQ             ?= $(SBOM_DIR)/requirements.dev.txt
SBOM_PROD_REQ_INPUT      ?=
SBOM_DEV_REQ_INPUT       ?=
PIP_AUDIT                ?= $(if $(ACT),$(ACT)/pip-audit,pip-audit)
SBOM_PIP_AUDIT           ?= $(VENV_PYTHON) -m pip_audit
SBOM_PIP_AUDIT_FLAGS     ?= --progress-spinner off --format $(SBOM_FORMAT)
PIP_AUDIT_FLAGS          ?= $(SBOM_PIP_AUDIT_FLAGS) $(SBOM_IGNORE_FLAGS)
SBOM_CACHE_DIR           ?= $(SBOM_DIR)/.cache
SBOM_CACHE_ENV           ?= XDG_CACHE_HOME="$(SBOM_CACHE_DIR)" PIP_CACHE_DIR="$(SBOM_CACHE_DIR)/pip"
SBOM_PROD_FILE            = $(SBOM_DIR)/$(PACKAGE_NAME)-$(SBOM_VERSION_SAFE)-$(GIT_SHA).prod.cdx.json
SBOM_DEV_FILE             = $(SBOM_DIR)/$(PACKAGE_NAME)-$(SBOM_VERSION_SAFE)-$(GIT_SHA).dev.cdx.json
SBOM_EXPORT_BASE          = $(UV) export --frozen --offline --package "$(PACKAGE_NAME)" --no-default-groups --no-emit-local --format requirements.txt
SBOM_RECURSIVE_MAKEFILE  ?= $(PACKAGE_PROFILE_MAKEFILE)
# pip-audit describes dependencies, so identify the package whose dependencies they are.
# An unknown dynamic version remains absent rather than being published as 0.0.0.
SBOM_IDENTIFY             = $(SBOM_METADATA_PYTHON) -c 'import json,sys; from pathlib import Path; p=Path(sys.argv[1]); d=json.loads(p.read_text(encoding="utf-8")); c={"type":"library","name":sys.argv[2]}; v=sys.argv[3]; c.update({"version":v} if v and v!="0.0.0" else {}); d.setdefault("metadata",{})["component"]=c; t=p.with_suffix(p.suffix+".tmp"); t.write_text(json.dumps(d,indent=2,sort_keys=True)+"\n",encoding="utf-8"); t.replace(p)'

define sbom_audit_and_identify
	@set +e; \
	staged="$(2).staging"; failed="$(2).failed"; \
	rm -f "$$staged" "$$failed"; \
	$(SBOM_CACHE_ENV) $(SBOM_PIP_AUDIT) $(PIP_AUDIT_FLAGS) -r "$(1)" --output "$$staged"; \
	audit_status=$$?; \
	if [ ! -s "$$staged" ]; then echo "✘ Missing SBOM output: $$staged"; exit 2; fi; \
	$(SBOM_IDENTIFY) "$$staged" "$(PACKAGE_NAME)" "$(SBOM_VERSION)"; \
	identity_status=$$?; \
	if [ $$identity_status -ne 0 ]; then mv "$$staged" "$$failed"; exit $$identity_status; fi; \
	if [ $$audit_status -ne 0 ]; then mv "$$staged" "$$failed"; exit $$audit_status; fi; \
	mv "$$staged" "$(2)"
endef

# A snapshot outside its source Git root needs a recorded commit and the
# relevant copied input hashes. The producer validates the record at use time.
SBOM_VERIFY_SNAPSHOT = $(SBOM_METADATA_PYTHON) -c 'import hashlib,json,re,sys; from pathlib import Path; root=Path(sys.argv[1]).resolve(); p=Path(sys.argv[2]); d=json.loads(p.read_text(encoding="utf-8")); commit=d.get("source_commit",""); describe=d.get("source_describe",""); sha=sys.argv[3]; raw=sys.argv[4]; package=sys.argv[5]; required={"pyproject.toml","uv.lock","makes/bijux-py/ci/sbom.mk",f"packages/{package}/pyproject.toml"}; hashes=d.get("input_sha256",{}); (d.get("schema")=="bijux-sbom-snapshot-v1" and d.get("source_repository") and re.fullmatch("[0-9a-f]{40}",commit) and isinstance(hashes,dict) and required.issubset(hashes)) or sys.exit("Invalid or incomplete SBOM snapshot provenance"); m=re.fullmatch("v[0-9]+\\.[0-9]+\\.[0-9]+-[0-9]+-g([0-9a-f]{7,40})",describe); (m and commit.startswith(m.group(1)) and len(sha)>=7 and commit.startswith(sha) and raw==describe) or sys.exit("SBOM snapshot commit/describe/SHA mismatch"); all(isinstance(k,str) and isinstance(v,str) and re.fullmatch("[0-9a-f]{64}",v) and (root/k).resolve().is_relative_to(root) and (root/k).is_file() and hashlib.sha256((root/k).read_bytes()).hexdigest()==v for k,v in hashes.items()) or sys.exit("SBOM snapshot input hash mismatch")'

define sbom_verify_candidate
	@if [ "$(SBOM_HAS_ROOT_GIT)" = 1 ]; then \
	  actual_head="$$(git -C "$(MONOREPO_ROOT)" rev-parse HEAD)"; \
	  actual_describe="$$(git -C "$(MONOREPO_ROOT)" describe --dirty --tags --long --match 'v[0-9]*')"; \
	  if ! printf '%s\n' "$(GIT_SHA)" | grep -Eq '^[0-9a-f]{7,40}$$'; then \
	    echo "✘ SBOM Git SHA is invalid"; exit 2; \
	  fi; \
	  case "$$actual_head" in "$(GIT_SHA)"*) ;; *) echo "✘ SBOM Git SHA disagrees with current candidate"; exit 2;; esac; \
	  if [ "$(SBOM_GIT_DESCRIBE_RAW)" != "$$actual_describe" ]; then \
	    echo "✘ SBOM Git description disagrees with current candidate"; exit 2; \
	  fi; \
	else \
	  $(SBOM_VERIFY_SNAPSHOT) "$(MONOREPO_ROOT)" "$(SBOM_SNAPSHOT_PROVENANCE)" "$(GIT_SHA)" "$(SBOM_GIT_DESCRIBE_RAW)" "$(PACKAGE_NAME)"; \
	fi
endef

define sbom_verify_identity
	$(sbom_verify_candidate)
	@if [ -z "$(SBOM_SCM_VERSION)" ]; then \
	  echo "✘ No supported clean SCM description for SBOM version"; \
	  exit 2; \
	fi
	@if [ "$(SBOM_VERSION)" != "$(SBOM_SCM_VERSION)" ]; then \
	  echo "✘ SBOM_VERSION disagrees with clean SCM version $(SBOM_SCM_VERSION)"; \
	  exit 2; \
	fi
endef

define sbom_check_tooling
	$(sbom_verify_identity)
	@if [ -n "$(strip $(SBOM_IGNORE_IDS))" ]; then \
	  echo "✘ Ungoverned SBOM vulnerability suppressions are forbidden: $(SBOM_IGNORE_IDS)"; \
	  exit 2; \
	fi
	@if ! "$(VENV_PYTHON)" -c "import pip_audit" >/dev/null 2>&1; then \
	  echo "→ Installing pip-audit into $(VENV)"; \
	  $(UV) pip install --python "$(VENV_PYTHON)" --upgrade pip-audit >/dev/null; \
	fi
endef

.PHONY: sbom sbom-dev sbom-prod sbom-summary sbom-validate sbom-clean sbom-tooling

sbom:
	@$(MAKE) -f "$(SBOM_RECURSIVE_MAKEFILE)" sbom-clean
	@$(MAKE) -f "$(SBOM_RECURSIVE_MAKEFILE)" sbom-prod
	@$(MAKE) -f "$(SBOM_RECURSIVE_MAKEFILE)" sbom-dev
	@$(MAKE) -f "$(SBOM_RECURSIVE_MAKEFILE)" sbom-summary
	@echo "✔ SBOMs generated in $(SBOM_DIR)"

sbom-tooling: | $(VENV_PYTHON)
	$(sbom_check_tooling)

sbom-prod:
	@mkdir -p "$(SBOM_DIR)" "$(SBOM_CACHE_DIR)"
	@rm -f "$(SBOM_DIR)"/*.prod.cdx.json "$(SBOM_DIR)/summary.txt"
	@$(MAKE) -f "$(PACKAGE_PROFILE_MAKEFILE)" "$(VENV_PYTHON)"
	$(sbom_check_tooling)
	@if [ -n "$(strip $(SBOM_REQUIREMENTS_WRITER))" ]; then \
	  $(SBOM_PYTHON_ENV) $(VENV_PYTHON) $(SBOM_REQUIREMENTS_WRITER) --pyproject "$(SBOM_PYPROJECT)" --group prod --output "$(SBOM_PROD_REQ)"; \
	elif [ -n "$(strip $(SBOM_PROD_REQ_INPUT))" ]; then \
	  test -f "$(SBOM_PROD_REQ_INPUT)" || { echo "✘ Missing production requirements input: $(SBOM_PROD_REQ_INPUT)"; exit 2; }; \
	  cp "$(SBOM_PROD_REQ_INPUT)" "$(SBOM_PROD_REQ)"; \
	else \
	  $(SBOM_EXPORT_BASE) --output-file "$(SBOM_PROD_REQ)" >/dev/null; \
	fi
	@test -s "$(SBOM_PROD_REQ)" || { echo "✘ Empty production requirements: $(SBOM_PROD_REQ)"; exit 2; }
	@echo "→ SBOM (prod via $(SBOM_PROD_REQ))"
	$(call sbom_audit_and_identify,$(SBOM_PROD_REQ),$(SBOM_PROD_FILE))

sbom-dev:
	@mkdir -p "$(SBOM_DIR)" "$(SBOM_CACHE_DIR)"
	@rm -f "$(SBOM_DIR)"/*.dev.cdx.json "$(SBOM_DIR)/summary.txt"
	@$(MAKE) -f "$(PACKAGE_PROFILE_MAKEFILE)" "$(VENV_PYTHON)"
	$(sbom_check_tooling)
	@if [ -n "$(strip $(SBOM_REQUIREMENTS_WRITER))" ]; then \
	  $(SBOM_PYTHON_ENV) $(VENV_PYTHON) $(SBOM_REQUIREMENTS_WRITER) --pyproject "$(SBOM_PYPROJECT)" --group dev --optional-group "$(SBOM_DEV_GROUP)" --output "$(SBOM_DEV_REQ)"; \
	elif [ -n "$(strip $(SBOM_DEV_REQ_INPUT))" ]; then \
	  test -f "$(SBOM_DEV_REQ_INPUT)" || { echo "✘ Missing development requirements input: $(SBOM_DEV_REQ_INPUT)"; exit 2; }; \
	  cp "$(SBOM_DEV_REQ_INPUT)" "$(SBOM_DEV_REQ)"; \
	else \
	  $(SBOM_EXPORT_BASE) --extra "$(SBOM_DEV_GROUP)" --output-file "$(SBOM_DEV_REQ)" >/dev/null; \
	fi
	@test -s "$(SBOM_DEV_REQ)" || { echo "✘ Empty development requirements: $(SBOM_DEV_REQ)"; exit 2; }
	@echo "→ SBOM (dev via $(SBOM_DEV_REQ))"
	$(call sbom_audit_and_identify,$(SBOM_DEV_REQ),$(SBOM_DEV_FILE))

sbom-validate:
	$(sbom_verify_identity)
	@if [ -z "$(SBOM_CLI)" ]; then echo "✘ SBOM_CLI not set"; exit 1; fi
	@command -v $(SBOM_CLI) >/dev/null 2>&1 || { echo "✘ '$(SBOM_CLI)' not found. Install it or set SBOM_CLI."; exit 1; }
	@for f in "$(SBOM_PROD_FILE)" "$(SBOM_DEV_FILE)"; do \
	  test -s "$$f" || { echo "✘ Missing current-candidate SBOM: $$f"; exit 2; }; \
	  echo "→ Validating $$f"; \
	  $(SBOM_CLI) validate --input-format json --input-file "$$f" || exit $$?; \
	done

sbom-summary:
	@mkdir -p "$(SBOM_DIR)"
	@rm -f "$(SBOM_DIR)/summary.txt"
	$(sbom_verify_identity)
	@echo "→ Writing SBOM summary"
	@"$(SBOM_METADATA_PYTHON)" -c 'import json,sys; from pathlib import Path; paths=[Path(p) for p in sys.argv[2:]]; missing=[str(p) for p in paths if not p.is_file() or not p.stat().st_size]; missing and sys.exit("Missing current-candidate SBOM: "+", ".join(missing)); lines=[p.name+"  components="+str(len(json.loads(p.read_text(encoding="utf-8")).get("components", []))) for p in paths]; Path(sys.argv[1]).write_text("\n".join(lines)+"\n",encoding="utf-8"); print("\n".join(lines))' "$(SBOM_DIR)/summary.txt" "$(SBOM_PROD_FILE)" "$(SBOM_DEV_FILE)"

sbom-clean:
	@echo "→ Cleaning SBOM artifacts"
	@mkdir -p "$(SBOM_DIR)"
	@rm -f "$(SBOM_DIR)"/*.cdx.json "$(SBOM_DIR)"/summary.txt "$(SBOM_DIR)"/requirements.*.txt || true
	@rm -rf "$(SBOM_CACHE_DIR)" || true

##@ SBOM
sbom:           ## Generate prod/dev SBOMs and a short summary
sbom-validate:  ## Validate all generated SBOMs with CycloneDX CLI
sbom-summary:   ## Write a brief components summary to $(SBOM_DIR)/summary.txt (best-effort)
sbom-clean:     ## Remove SBOM artifacts from $(SBOM_DIR)
