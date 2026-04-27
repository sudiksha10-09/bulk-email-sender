"""
Cold Email Generator — standalone module.
To remove: delete apps/email_generator/, remove 2 lines from config/urls.py
"""
import json
import csv
import io
import logging
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from pathlib import Path

logger = logging.getLogger(__name__)


def generator_page(request):
    """Serve the email generator frontend page."""
    html = (Path(settings.BASE_DIR) / 'frontend' / 'generator.html').read_text(encoding='utf-8')
    return HttpResponse(html)


@csrf_exempt
@require_http_methods(["POST"])
def generate_emails(request):
    """
    POST /generator/api/generate
    Generate personalized cold emails using Claude or OpenAI.
    Body: {
        "role": "Frontend Developer",
        "skills": "React, TypeScript, Node.js",
        "experience": "2 years",
        "companies": ["Google", "Stripe", "Razorpay"],
        "tone": "professional|friendly|concise",
        "goal": "job|freelance|collab"
    }
    """
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    role = data.get('role', '').strip()
    skills = data.get('skills', '').strip()
    experience = data.get('experience', '').strip()
    companies = data.get('companies', [])
    tone = data.get('tone', 'professional')
    goal = data.get('goal', 'job')

    if not role or not skills or not companies:
        return JsonResponse({'error': 'role, skills, and companies are required'}, status=400)

    if len(companies) > 50:
        return JsonResponse({'error': 'Maximum 50 companies per request'}, status=400)

    goal_text = {
        'job': 'a full-time job opportunity',
        'freelance': 'freelance/contract work',
        'collab': 'a collaboration or open source contribution',
    }.get(goal, 'a job opportunity')

    tone_text = {
        'professional': 'professional and formal',
        'friendly': 'warm, friendly, and conversational',
        'concise': 'very concise and direct (under 100 words)',
    }.get(tone, 'professional')

    emails = []
    api_key = getattr(settings, 'ANTHROPIC_API_KEY', '') or getattr(settings, 'OPENAI_API_KEY', '')

    if not api_key:
        # Demo mode — generate template emails without AI
        for company in companies:
            emails.append(_demo_email(role, skills, experience, company, goal_text))
        return JsonResponse({'emails': emails, 'mode': 'demo'})

    # Try Claude first, fall back to OpenAI
    try:
        emails = _generate_with_claude(role, skills, experience, companies, goal_text, tone_text)
        return JsonResponse({'emails': emails, 'mode': 'ai'})
    except Exception as e:
        logger.warning(f"Claude failed: {e}, trying demo mode")
        for company in companies:
            emails.append(_demo_email(role, skills, experience, company, goal_text))
        return JsonResponse({'emails': emails, 'mode': 'demo'})


def _generate_with_claude(role, skills, experience, companies, goal_text, tone_text):
    """Generate emails using Claude API."""
    import anthropic
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    emails = []
    for company in companies:
        prompt = f"""Write a cold outreach email for {goal_text} at {company}.

Sender profile:
- Role: {role}
- Skills: {skills}
- Experience: {experience or 'not specified'}

Requirements:
- Tone: {tone_text}
- Mention {company} specifically (why you want to work there)
- Highlight 2-3 most relevant skills
- Clear call to action
- Subject line on first line as "Subject: ..."
- Then blank line, then email body
- Keep it under 200 words
- Do NOT use placeholders like [Your Name] — use "I" and sign off as "Best regards"

Write only the email, nothing else."""

        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}]
        )
        text = message.content[0].text.strip()
        subject, body = _parse_email(text)
        emails.append({
            'company': company,
            'subject': subject,
            'body': body,
            'full': text,
        })

    return emails


def _demo_email(role, skills, experience, company, goal_text):
    """Generate a template email without AI (demo/fallback mode)."""
    skill_list = [s.strip() for s in skills.split(',')][:3]
    skills_str = ', '.join(skill_list)
    exp_str = f" with {experience} of experience" if experience else ""

    subject = f"Exploring {goal_text.split()[0].capitalize()} Opportunities at {company}"
    body = f"""Hi {company} Team,

I'm a {role}{exp_str} skilled in {skills_str}. I've been following {company}'s work and I'm genuinely excited about the problems you're solving.

I'd love to explore if there's an opportunity to contribute to your team. I'm confident my background in {skill_list[0]} would add value to your engineering efforts.

Would you be open to a quick 15-minute call this week?

Best regards"""

    return {
        'company': company,
        'subject': subject,
        'body': body,
        'full': f"Subject: {subject}\n\n{body}",
    }


def _parse_email(text):
    """Extract subject and body from generated text."""
    lines = text.strip().split('\n')
    subject = ''
    body_lines = []
    found_subject = False

    for i, line in enumerate(lines):
        if line.lower().startswith('subject:'):
            subject = line[8:].strip()
            found_subject = True
        elif found_subject and line.strip() == '' and not body_lines:
            continue  # skip blank line after subject
        elif found_subject:
            body_lines.append(line)

    if not subject:
        subject = 'Exploring Opportunities'
        body_lines = lines

    return subject, '\n'.join(body_lines).strip()


@csrf_exempt
@require_http_methods(["POST"])
def export_csv(request):
    """
    POST /generator/api/export
    Export generated emails as CSV.
    Body: { "emails": [...] }
    """
    try:
        data = json.loads(request.body)
        emails = data.get('emails', [])
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    if not emails:
        return JsonResponse({'error': 'No emails to export'}, status=400)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['company', 'subject', 'body'])
    for e in emails:
        writer.writerow([e.get('company', ''), e.get('subject', ''), e.get('body', '')])

    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="cold_emails.csv"'
    return response
