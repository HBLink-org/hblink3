# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.2] - 2025-12-14

### Changed
- Updated Dockerfile base image from Alpine 3.18 to Alpine 3.20 for better compatibility with modern systems
- Updated GitHub Actions workflow to use current versions (checkout@v4, docker/setup-buildx-action@v3, docker/login-action@v3)
- Modernized docker-compose.yml by removing obsolete version field
- Updated Python dependency minimum versions for Debian 13 and Python 3.11/3.12 compatibility:
  - bitstring: 3.1.9 → 4.0.0
  - bitarray: 2.3.5 → 2.8.0
  - Twisted: 21.7.0 → 24.0.0
  - configparser: 5.2.0 → 7.0.0

### Fixed
- Fixed POSIX compliance in entrypoint script (changed `==` to `=` for shell comparison)
- Added error handling to `cd` command in entrypoint script

### Security
- Updated all GitHub Actions to latest versions for improved security
- Verified no security vulnerabilities in updated dependencies

## [1.6.10] - Previous Release

### Note
- This changelog was added as part of Debian 13 compatibility updates
- For changes prior to this version, please refer to git commit history
