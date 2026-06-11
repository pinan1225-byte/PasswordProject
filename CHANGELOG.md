# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **AI-Powered Multimodal Import**: Support extracting account assets from text, image screenshots (via macOS native Vision OCR) and audio recordings (via macOS Speech ASR), parsing them into JSON using SenseAuto-Chat-v6 with automatic field normalization and interactive preview editing.
- **macOS Standalone Application (.app)**: Add bundling script (`build_mac_app.sh`) utilizing native `sips` and `iconutil` to generate high-resolution `.icns` icons, packaging with built-in configuration and resource path redirection for zero-config drag-and-drop launch.
- **PyQt6 Async Threading Refactor**: Deconstruct database I/O and cryptographic calculations into separate background worker threads (`LoginThread`, `LoadPasswordsThread`, etc.) to guarantee a 100% smooth, freeze-free UI experience.
- **Dynamic Password Generator Dialog**: Refactor password generation out of main tab into an independent dialog supporting random, keyword and AI modes with smooth height auto-resizing to prevent UI element squeezing.
- **First Column Width Auto-Fitting**: Support interactive resizing for first column and automatically scale column width based on text content (bounded 200px ~ 450px) to prevent long titles from being truncated.
- Initial project structure
- Core encryption module with AES-256-GCM
- Password generation with configurable policies
- Password strength evaluation
- MySQL database integration
- CLI interface for vault management
- Category and tag support
- Search functionality
- Soft delete feature

### Security
- PBKDF2 key derivation with 100,000 iterations
- Cryptographically secure random number generation
- Encryption key memory clearing
- No sensitive data in logs

## [0.1.0] - 2026-03-31

### Added
- Initial release
- Basic password encryption and storage
- Password generation functionality
- MySQL database backend
- Command-line interface
- Configuration management
- Unit and integration tests
- CI/CD pipeline
- Security documentation

### Security
- AES-256-GCM encryption
- PBKDF2-SHA256 key derivation
- Secure password hashing
- Memory-safe key handling

---

## Version History

- **0.1.0** (2026-03-31): Initial release with core features