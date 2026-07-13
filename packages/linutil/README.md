# Linutil

This package builds the upstream Linutil Rust workspace from the
`2026.05.21` release tag. It installs the `linutil` terminal application,
desktop entry, and manual page.

## Vendored dependencies

COPR binary builds run without network access, so `linutil.spec` uses a
target-filtered archive of the dependencies pinned in upstream's
`Cargo.lock`. To regenerate it with `cargo-vendor-filterer`:

```bash
cargo install cargo-vendor-filterer --version 0.5.18 --locked
git clone --branch 2026.05.21 --depth 1 \
  https://github.com/ChrisTitusTech/linutil.git linutil-2026.05.21
cargo vendor-filterer \
  --manifest-path linutil-2026.05.21/Cargo.toml \
  --platform x86_64-unknown-linux-gnu \
  --versioned-dirs \
  --format tar.zstd \
  --prefix vendor \
  linutil-vendor-26.5.21.tar.zst
```

The expected SHA-256 digest is
`9ed146276ccd9a561ef9055645f86e6d3581c009a94e398dfe9933192e7a5d3b`.

The archive is intentionally restricted to x86_64 because this COPR's
configured chroots are x86_64-only.
