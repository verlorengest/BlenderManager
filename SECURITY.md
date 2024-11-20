### **Security Policy for Blender Manager**

**Effective Date:** -
**Last Updated:** -

This document outlines the security practices and procedures for the Blender Manager application to ensure the safety, integrity, and privacy of its users.

---

### **1. Supported Versions**
We actively support the latest stable release of Blender Manager. Critical security patches will also be applied to the two most recent versions. 

| Version        | Supported          |  
|----------------|--------------------|  
| Latest Release | ✅ Yes             |  
| Last - 1       | ✅ Yes             |  
| Last - 2       | ✅ Yes             |  

Older versions will not receive security updates. Users are encouraged to upgrade to a supported version to ensure protection against vulnerabilities.

---

### **2. Reporting a Vulnerability**
If you discover a security vulnerability, we urge you to report it as soon as possible. 

**Steps to Report:**
1. Send a detailed email to **[Developer](mailto:kaansoyler@proton.me)**.
2. Include:
   - A description of the issue and its potential impact.
   - Steps to reproduce the vulnerability.
   - Any potential mitigation or patch suggestions.
   - Your contact information for follow-up.

**Responsible Disclosure:**  
Please do not publicly disclose the vulnerability until we have had adequate time to address it. We aim to confirm receipt of your report within 48 hours and provide an initial assessment within 5 business days.

---

### **3. Response Timeline**
Our team is committed to promptly addressing reported vulnerabilities. Below is our typical response timeline:

| Phase                          | Timeframe        |  
|--------------------------------|-----------------|  
| Acknowledgement of report      | 48 hours        |  
| Initial assessment             | 5 business days |  
| Development of a patch         | As soon as feasible, depending on severity |  
| Release of security patch      | Within 14 days of confirmed vulnerability, if feasible |  

In critical cases, a hotfix may be released sooner.

---

### **4. Security Measures**
Blender Manager incorporates several layers of security to safeguard user data and maintain system integrity:

- **Data Protection:** Blender Manager does not store or transmit sensitive data. Any user preferences or configurations are saved locally within the user environment.  
- **Dependency Management:** The application is built using trusted Python libraries and dependencies. Regular audits are performed to ensure no vulnerabilities exist in third-party components.  
- **Access Control:** Features that interact with the system (e.g., file management, updates) operate under least privilege principles, minimizing the risk of unintended actions.  
- **Code Validation:** All contributions to Blender Manager undergo code review to ensure adherence to security best practices.

---

### **5. Security Best Practices for Contributors**
Contributors to Blender Manager must adhere to the following guidelines to maintain the security of the application:

1. **Secure Coding Practices:** Write secure, maintainable code that avoids common vulnerabilities (e.g., SQL injection, buffer overflow).  
2. **Dependency Management:** Ensure all dependencies are sourced from trusted repositories and are actively maintained.  
3. **Code Reviews:** Submit all code changes via pull requests, ensuring they are reviewed by at least one other contributor.  
4. **Secrets Management:** Avoid hardcoding sensitive information, such as API keys, in the codebase. Use environment variables instead.  
5. **Testing:** Run security tests and address any issues before merging changes into the main branch.

---

### **6. Scope**
This policy covers:
- The Blender Manager application and all associated tools.
- All dependencies directly used by Blender Manager.  

This policy does **not** cover:
- Third-party addons used within Blender Manager unless explicitly listed as supported.
- External tools or scripts interacting with Blender Manager.

---

### **7. Contact Information**
For any security-related concerns or questions, please contact us:  
**[E-Mail](mailto:kaansoyler@proton.me)** 
**[GitHub](https://github.com/verlorengest/BlenderManager)** (For non-sensitive issues only)

---

### **8. Acknowledgments**
We appreciate and acknowledge the efforts of the security research community in helping us improve Blender Manager’s security.

Thank you for helping us maintain a safe and reliable application for everyone.
