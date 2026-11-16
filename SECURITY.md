# Security Policy

BoundaryBench is a local, synthetic, non-destructive research framework. It is
intended to be pointed only at its own synthetic applications and, when
explicitly configured, at targets you are authorized to test.

## Reporting a vulnerability

If you discover a security issue in BoundaryBench itself (for example, a way
that the framework contacts an unintended network destination, or a path that
could exfiltrate a real credential), please report it privately rather than
opening a public issue.

Open a private security advisory on the GitHub repository, or contact the
maintainer directly. Include:

- A description of the behavior and its impact.
- Reproduction steps against the synthetic application.
- The BoundaryBench version and Python version.

## What this project is not

- BoundaryBench is not a general-purpose scanner and does not claim to find
  vulnerabilities in arbitrary production systems.
- It does not ship real attack payloads, real credentials, or real targets.
- The vulnerable synthetic application is intentionally insecure and is not a
  template for production code.
