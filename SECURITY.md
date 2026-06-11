# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of this password manager seriously. If you discover a security vulnerability, please follow these steps:

### How to Report

1. **DO NOT** open a public issue on GitHub
2. Email security concerns to: security@example.com
3. Include the following information:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if available)

### What to Expect

- **Acknowledgment**: Within 24 hours
- **Initial Assessment**: Within 72 hours
- **Status Updates**: Every 7 days until resolved
- **Resolution Timeline**: Critical vulnerabilities within 7 days

### Security Measures

This project implements the following security measures:

#### Encryption
- AES-256-GCM for data encryption
- PBKDF2-SHA256 for key derivation (100,000 iterations)
- Cryptographically secure random number generation

#### Data Protection
- Master password never stored in plaintext
- Encryption keys cleared from memory after use
- No sensitive data in logs
- Secure session management

#### Access Control
- Master password required for all operations
- Configurable session timeout
- Maximum login attempts before lockout

#### Code Security
- Regular dependency updates
- Automated security scanning in CI/CD
- Code review required for all changes
- Pre-commit hooks for security checks

## Security Best Practices

### For Users

1. **Use a Strong Master Password**
   - Minimum 16 characters
   - Mix of uppercase, lowercase, numbers, and symbols
   - Avoid common words or patterns

2. **Keep Your Master Password Secret**
   - Never share your master password
   - Don't write it down in plain text
   - Consider using a memorable passphrase

3. **Regular Backups**
   - Export encrypted vault regularly
   - Store backups in secure location
   - Test backup restoration

4. **Environment Security**
   - Keep your system updated
   - Use antivirus software
   - Be cautious of phishing attempts

### For Developers

1. **Code Review**
   - All code changes require review
   - Security-sensitive code needs additional review
   - Follow secure coding guidelines

2. **Dependency Management**
   - Keep dependencies updated
   - Monitor for security advisories
   - Use dependency scanning tools

3. **Testing**
   - Write comprehensive tests
   - Include security test cases
   - Test encryption/decryption thoroughly

4. **Documentation**
   - Document security features
   - Keep security documentation updated
   - Report security-relevant changes

## Security Checklist

Before deploying to production:

- [ ] Change default MASTER_KEY_SALT
- [ ] Use strong MySQL password
- [ ] Enable SSL for database connections
- [ ] Configure firewall rules
- [ ] Set up regular backups
- [ ] Enable audit logging
- [ ] Review environment variables
- [ ] Run security scans
- [ ] Perform penetration testing

## Known Security Considerations

### Current Limitations

1. **Single Factor Authentication**
   - Only master password protects the vault
   - Future: Plan to add 2FA support

2. **Local Storage**
   - Database stored locally
   - Future: Cloud sync with end-to-end encryption

3. **Clipboard Security**
   - Passwords may remain in clipboard
   - Users should clear clipboard after use

### Threat Model

**Protected Against:**
- Database theft (encrypted data)
- Memory dumps (keys cleared)
- Brute force (PBKDF2 with high iterations)
- Rainbow tables (unique salts)

**Not Protected Against:**
- Keyloggers on user's machine
- Compromised operating system
- Physical access to unlocked session
- Social engineering attacks

## Security Updates

Security updates will be released as patch versions and announced through:
- GitHub Security Advisories
- Release notes
- Email notifications (for critical issues)

## Contact

For security concerns:
- Email: security@example.com
- PGP Key: [Link to public key]

For general questions:
- GitHub Issues: For non-security bugs
- Discussions: For general questions

---

**Last Updated**: 2026-03-31
**Next Review**: 2026-06-31