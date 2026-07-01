import json
from django.views import View
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from anthropic import Anthropic


class AIAssistView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        if not settings.ANTHROPIC_API_KEY or settings.ANTHROPIC_API_KEY == "your-key-here":
            return JsonResponse({
                "error": "Anthropic API key is not configured. Please add a valid ANTHROPIC_API_KEY to your .env file."
            }, status=400)

        try:
            data = json.loads(request.body)
            action = data.get("action")
            text = data.get("text", "")
            tone = data.get("tone", "")
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON payload"}, status=400)

        if not text:
            return JsonResponse({"error": "Text content is required"}, status=400)

        # Construct prompt based on action
        system_instruction = "You are an AI writing assistant integrated into a blog CMS. Follow instructions precisely."
        user_prompt = ""

        if action == "improve":
            user_prompt = (
                "Improve the writing of the following text to make it clearer, more polished, and more engaging. "
                "Retain the original meaning, style, and formatting (like markdown) where appropriate. "
                "Return ONLY the improved text. Do not include any introductory text, preamble, "
                "explanation, or conversational remarks.\n\n"
                f"Text:\n{text}"
            )
        elif action == "continue":
            user_prompt = (
                "Here is the trailing end of a blog post. Continue writing the post naturally for another 2 to 3 paragraphs. "
                "Ensure a seamless flow from the existing text and output the response in standard Markdown format. "
                "Return ONLY the continuation paragraphs. Do not include any introductory remarks, preamble, explanations, "
                "or conversational filler.\n\n"
                f"Trailing text:\n{text}"
            )
        elif action == "grammar":
            user_prompt = (
                "Fix all grammar, punctuation, spelling, and typos in the following text. "
                "Do not rewrite or change the author's tone/voice; only correct actual errors. "
                "Return ONLY the corrected text. Do not include any introductory text, preamble, "
                "explanations, or conversational filler.\n\n"
                f"Text:\n{text}"
            )
        elif action == "tone":
            if not tone:
                return JsonResponse({"error": "Tone is required for tone adjustments"}, status=400)
            user_prompt = (
                f"Rewrite the following text in a clear '{tone}' tone. Maintain the underlying message "
                "but adjust vocabulary, phrasing, and style to match the target tone. "
                "Return ONLY the rewritten version. Do not include any introductory text, preamble, "
                "explanations, or conversational filler.\n\n"
                f"Text:\n{text}"
            )
        else:
            return JsonResponse({"error": f"Unknown action: {action}"}, status=400)

        try:
            client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            message = client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=1500,
                temperature=0.7,
                system=system_instruction,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            # Retrieve the result text from message content block(s)
            result_text = "".join([block.text for block in message.content])
            
            # Simple estimate: 1 token is roughly 4 characters
            input_tokens = len(user_prompt) // 4
            output_tokens = len(result_text) // 4
            
            return JsonResponse({
                "result": result_text.strip(),
                "input_tokens_est": input_tokens,
                "output_tokens_est": output_tokens
            })
        except Exception as e:
            return JsonResponse({"error": f"Anthropic API Call Failed: {str(e)}"}, status=500)


class AISummarizeView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        if not settings.ANTHROPIC_API_KEY or settings.ANTHROPIC_API_KEY == "your-key-here":
            return JsonResponse({
                "error": "Anthropic API key is not configured. Please add a valid ANTHROPIC_API_KEY to your .env file."
            }, status=400)

        try:
            data = json.loads(request.body)
            content = data.get("content", "")
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON payload"}, status=400)

        if not content:
            return JsonResponse({"error": "Content is required for summarization"}, status=400)

        user_prompt = (
            "Summarize this blog post in 2-3 sentences, suitable as a meta description. "
            "Be concise and compelling. Return only the summary, no preamble.\n\n"
            f"Content:\n{content}"
        )

        try:
            client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            message = client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=300,
                temperature=0.5,
                system="You are an AI summary assistant. Return only the direct summary text.",
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            summary_text = "".join([block.text for block in message.content])
            return JsonResponse({"summary": summary_text.strip()})
        except Exception as e:
            return JsonResponse({"error": f"Anthropic API Call Failed: {str(e)}"}, status=500)
