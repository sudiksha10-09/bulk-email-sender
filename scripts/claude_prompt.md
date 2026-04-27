# Claude Prompt — Generate Email List + Cold Email Body

Paste this into Claude (claude.ai) and fill in the [brackets]:

---

## PROMPT:

I'm doing cold outreach for job applications. Help me with two things:

**1. Generate a CSV of target companies**

Create a CSV with these exact columns: `email,name,company,role,location`

Find [20] companies in the [software / fintech / startup] space that are likely hiring [Full Stack Developers].
Use realistic HR/recruiter email formats like hr@company.com, careers@company.com, or talent@company.com.

Format the output as a plain CSV I can copy and save as a .csv file. Example:
```
email,name,company,role,location
hr@acmecorp.com,Hiring Manager,Acme Corp,Full Stack Developer,Bangalore
careers@techstartup.io,Recruiter,TechStartup,Backend Developer,Remote
```

**2. Write a cold outreach email template**

Write a professional cold email for a [Full Stack Developer] job application.
- Use `{{name}}` for the recipient's name
- Use `{{company}}` for the company name
- Use `{{role}}` for the role they're hiring for
- Keep it under 150 words — short and direct
- Mention I'm attaching my resume
- Sound human, not like a template
- End with my name: [Your Name]

Return the subject line and body separately.

---

## WHAT TO DO WITH THE OUTPUT:

1. Copy the CSV block → save as `recipients.csv`
2. Upload `recipients.csv` in BulkMail → Recipients tab
3. Copy the subject line → paste into BulkMail subject field
4. Copy the email body → paste into BulkMail email editor
5. Attach your resume → hit Send
