# SecureLink

SecureLink is a backend service designed to shorten user-provided URLs while enhancing link safety through automated security analysis. The system generates compact redirect codes, evaluates URLs for potentially malicious characteristics, assigns a risk score, and classifies links based on their threat level before they are shared.

Built with FastAPI and MongoDB, SecureLink provides RESTful APIs for creating, listing, retrieving, and deleting shortened URLs. The service also supports redirect handling, QR code generation, click analytics tracking, and abuse reporting for suspicious or malicious links.

Key Features:

* URL shortening with unique short codes
* Automated URL security analysis and risk classification
* Risk scoring based on URL characteristics and suspicious patterns
* QR code generation for shortened links
* Redirect management with safety checks
* Click analytics and usage tracking
* Abuse reporting system for phishing, malware, spam, and scam links
* MongoDB-based data storage
* REST API architecture using FastAPI
* Local testing support through a command-line utility for dry-run URL shortening without starting the HTTP server

The project is currently designed for local development and testing on localhost, with a deployment roadmap that includes cloud hosting and frontend integration in future stages.
