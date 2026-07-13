# COPR invokes this target from the package subdirectory and supplies outdir
# and spec. Keep this target usable both in COPR and in local validation.
.PHONY: srpm

srpm:
	@set -eu; \
	if ! command -v rpmbuild >/dev/null 2>&1 || ! command -v spectool >/dev/null 2>&1; then \
		if command -v dnf >/dev/null 2>&1; then \
			dnf -y install rpm-build rpmdevtools; \
		else \
			printf '%s\n' 'rpmbuild and spectool are required' >&2; \
			exit 1; \
		fi; \
	fi; \
	test -n "$(outdir)" || { printf '%s\n' 'outdir is required' >&2; exit 2; }; \
	test -n "$(spec)" || { printf '%s\n' 'spec is required' >&2; exit 2; }; \
	mkdir -p "$(outdir)"; \
	spectool -g -C "$(CURDIR)" "$(spec)"; \
	rpmbuild -bs "$(spec)" \
		--define "_sourcedir $(CURDIR)" \
		--define "_srcrpmdir $(abspath $(outdir))"

