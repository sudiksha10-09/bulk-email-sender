"""Claude AI integration utilities."""
import time
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def get_claude_client():
    """Get Anthropic Claude client."""
    try:
        import anthropic
        api_key = settings.ANTHROPIC_API_KEY
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not configured")
        return anthropic.Anthropic(api_key=api_key)
    except ImportError:
        raise ImportError("anthropic package not installed")


def call_claude_with_retry(prompt, max_retries=3, timeout=10):
    """
    Call Claude API with exponential backoff retry logic.

    Returns:
        str: The response text
    Raises:
        Exception: If all retries fail
    """
    import anthropic

    client = get_claude_client()
    last_error = None

    for attempt in range(max_retries):
        try:
            message = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1024,
                timeout=timeout,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text

        except anthropic.RateLimitError as e:
            last_error = e
            wait_time = (2 ** attempt) * 5  # 5s, 10s, 20s
            logger.warning(f"Claude rate limit hit, waiting {wait_time}s (attempt {attempt + 1})")
            time.sleep(wait_time)

        except anthropic.APITimeoutError as e:
            last_error = e
            logger.warning(f"Claude timeout on attempt {attempt + 1}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)

        except anthropic.APIStatusError as e:
            last_error = e
            if e.status_code >= 500:
                wait_time = 2 ** attempt
                logger.warning(f"Claude server error {e.status_code}, retrying in {wait_time}s")
                time.sleep(wait_time)
            else:
                raise  # Don't retry 4xx errors

        except Exception as e:
            last_error = e
            logger.error(f"Unexpected Claude error: {e}")
            raise

    raise Exception(f"Claude API failed after {max_retries} attempts: {last_error}")


def generate_subject_lines(email_body, context=None):
    """
    Generate 5 subject line alternatives using Claude.

    Returns:
        list[str]: Exactly 5 subject lines
    Raises:
        Exception: If AI service fails
    """
    context_str = f"\nAdditional context: {context}" if context else ""
    prompt = f"""You are an email marketing expert. Generate exactly 5 compelling subject lines for the following email body.

Email body:
{email_body}
{context_str}

Requirements:
- Generate exactly 5 subject lines
- Each should be engaging and optimized for open rates
- Keep each under 60 characters
- Vary the tone and approach
- Number each line 1-5

Format your response as:
1. [subject line]
2. [subject line]
3. [subject line]
4. [subject line]
5. [subject line]"""

    response = call_claude_with_retry(prompt)

    # Parse numbered list
    lines = []
    for line in response.strip().split('\n'):
        line = line.strip()
        if line and line[0].isdigit() and '. ' in line:
            subject = line.split('. ', 1)[1].strip()
            if subject:
                lines.append(subject)

    # Ensure exactly 5
    if len(lines) < 5:
        # Pad with generic subjects if parsing failed
        while len(lines) < 5:
            lines.append(f"Subject line option {len(lines) + 1}")
    return lines[:5]


def personalize_email(template_body, recipient_metadata):
    """
    Personalize email content for a specific recipient using Claude.

    Returns:
        str: Personalized email body
    """
    metadata_str = ', '.join(f"{k}: {v}" for k, v in recipient_metadata.items() if v)
    prompt = f"""You are an email personalization expert. Personalize the following email template for a specific recipient.

Template:
{template_body}

Recipient information:
{metadata_str}

Instructions:
- Maintain the core message and structure
- Adapt the tone and specific details to feel personal and relevant
- Use the recipient's information naturally
- Keep the same approximate length
- Return only the personalized email body, no explanations

Personalized email:"""

    return call_claude_with_retry(prompt)


def analyze_spam_score(subject, body):
    """
    Analyze email content for spam likelihood using Claude.

    Returns:
        dict: { score: int, recommendations: list, trigger_words: list }
    """
    prompt = f"""You are an email deliverability expert. Analyze the following email for spam likelihood.

Subject: {subject}

Body:
{body}

Provide a deliverability analysis in this exact JSON format:
{{
  "score": <integer 0-100, where 100 is best deliverability>,
  "recommendations": [<list of specific improvement suggestions>],
  "trigger_words": [<list of spam trigger words found in the email>]
}}

Return only valid JSON, no other text."""

    import json
    response = call_claude_with_retry(prompt)

    try:
        # Extract JSON from response
        response = response.strip()
        if response.startswith('```'):
            response = response.split('```')[1]
            if response.startswith('json'):
                response = response[4:]
        result = json.loads(response)

        # Validate and clamp score
        score = max(0, min(100, int(result.get('score', 50))))
        recommendations = result.get('recommendations', [])
        trigger_words = result.get('trigger_words', [])

        return {
            'score': score,
            'recommendations': recommendations if isinstance(recommendations, list) else [],
            'trigger_words': trigger_words if isinstance(trigger_words, list) else [],
        }
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.error(f"Failed to parse spam analysis response: {e}")
        return {
            'score': 50,
            'recommendations': ['Unable to parse AI response. Please try again.'],
            'trigger_words': [],
        }
