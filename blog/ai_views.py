import json
from django.views import View
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.utils.text import slugify
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.core.cache import cache
from anthropic import Anthropic
from .models import Tag, Post


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


class AITagSuggestView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        if not settings.ANTHROPIC_API_KEY or settings.ANTHROPIC_API_KEY == "your-key-here":
            return JsonResponse({
                "error": "Anthropic API key is not configured. Please add a valid ANTHROPIC_API_KEY to your .env file."
            }, status=400)

        try:
            data = json.loads(request.body)
            title = data.get("title", "")
            content = data.get("content", "")
            summary = data.get("summary", "")
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON payload"}, status=400)

        user_prompt = (
            "Suggest 3-5 relevant tags for this blog post.\n"
            f"Title: {title}\n"
            f"Summary: {summary}\n"
            f"Content: {content[:2000]}\n\n"
            "Return ONLY a JSON array of tag names, lowercase, no spaces (use hyphens). "
            "Example: [\"django\", \"web-dev\", \"python-tips\"]"
        )

        try:
            client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            message = client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=200,
                temperature=0.4,
                system="You are an AI tag suggest helper. Return only the raw JSON array string.",
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            raw_result = "".join([block.text for block in message.content]).strip()
            
            # Clean possible markdown wrapping
            if raw_result.startswith("```"):
                lines = raw_result.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].startswith("```"):
                    lines = lines[:-1]
                raw_result = "\n".join(lines).strip()
            
            tags_list = json.loads(raw_result)
            if not isinstance(tags_list, list):
                return JsonResponse({"error": "Claude response was not a valid list"}, status=500)
                
            # Sanitize tags list to lowercase and strip spaces
            cleaned_tags = [str(tag).lower().replace(" ", "-").strip() for tag in tags_list if tag]
            return JsonResponse({"tags": cleaned_tags})
        except json.JSONDecodeError:
            return JsonResponse({"error": f"Failed to parse Claude output: {raw_result}"}, status=500)
        except Exception as e:
            return JsonResponse({"error": f"Anthropic API Call Failed: {str(e)}"}, status=500)


class AICreateTagView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            name = data.get("name", "").strip()
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON payload"}, status=400)

        if not name:
            return JsonResponse({"error": "Tag name is required"}, status=400)

        # Sanitize and slugify
        name_clean = name.lower().replace(" ", "-")
        slug = slugify(name_clean)
        
        tag, created = Tag.objects.get_or_create(name=name_clean, defaults={"slug": slug})
        return JsonResponse({"id": tag.id, "name": tag.name})


class AIRelatedView(View):
    def get(self, request, slug, *args, **kwargs):
        try:
            current_post = Post.objects.select_related("author").prefetch_related("tags").get(slug=slug)
        except Post.DoesNotExist:
            return JsonResponse({"error": "Post not found"}, status=404)

        cache_key = f"related_posts_{current_post.slug}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return JsonResponse(cached_result)

        # Get all other published posts
        other_posts = Post.objects.filter(status="published").exclude(pk=current_post.pk).only("title", "slug", "summary")
        if not other_posts.exists():
            return JsonResponse({"related": [], "posts": {}})

        # If there are only a few other posts, return them directly
        if other_posts.count() <= 4:
            ranked_slugs = list(other_posts.values_list("slug", flat=True))
            return self._build_response(ranked_slugs, current_post.slug, cache_key)

        title = current_post.title
        summary = current_post.summary
        tags_str = ", ".join([t.name for t in current_post.tags.all()])

        posts_data = [{"title": p.title, "slug": p.slug, "summary": p.summary} for p in other_posts]
        posts_json = json.dumps(posts_data)

        user_prompt = (
            f"Given this reference post:\n"
            f"Title: {title}\n"
            f"Summary: {summary}\n"
            f"Tags: {tags_str}\n\n"
            f"From the following JSON list of other posts:\n"
            f"{posts_json}\n\n"
            f"Rank the top 4 most semantically related posts from the list. "
            f"Return ONLY a JSON array of the top 4 post slugs. Return nothing else, no markdown formatting."
        )

        try:
            client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            message = client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=250,
                temperature=0.3,
                system="You are a related content ranker. Output only a raw JSON array of slugs.",
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            raw_result = "".join([block.text for block in message.content]).strip()

            if raw_result.startswith("```"):
                lines = raw_result.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].startswith("```"):
                    lines = lines[:-1]
                raw_result = "\n".join(lines).strip()

            ranked_slugs = json.loads(raw_result)
            if not isinstance(ranked_slugs, list):
                raise ValueError("Claude output is not a list")
        except Exception:
            # Fallback to tag-based overlap
            current_tags = current_post.tags.all()
            if current_tags.exists():
                fallback_posts = Post.objects.filter(status="published", tags__in=current_tags).exclude(pk=current_post.pk).distinct()[:4]
            else:
                fallback_posts = Post.objects.filter(status="published").exclude(pk=current_post.pk)[:4]
            ranked_slugs = list(fallback_posts.values_list("slug", flat=True))

        return self._build_response(ranked_slugs, current_post.slug, cache_key)

    def _build_response(self, ranked_slugs, current_slug, cache_key):
        posts_qs = Post.objects.filter(slug__in=ranked_slugs, status="published")
        posts_map = {p.slug: p for p in posts_qs}

        ordered_slugs = []
        posts_details = {}
        for s in ranked_slugs:
            if s in posts_map:
                p = posts_map[s]
                ordered_slugs.append(s)
                posts_details[s] = {
                    "title": p.title,
                    "url": p.get_absolute_url(),
                    "reading_time": p.reading_time,
                    "view_count": p.view_count
                }

        # Backfill if we have fewer than 4 related posts
        if len(ordered_slugs) < 4:
            extra_posts = Post.objects.filter(status="published").exclude(slug__in=ordered_slugs).exclude(slug=current_slug)[:4 - len(ordered_slugs)]
            for p in extra_posts:
                ordered_slugs.append(p.slug)
                posts_details[p.slug] = {
                    "title": p.title,
                    "url": p.get_absolute_url(),
                    "reading_time": p.reading_time,
                    "view_count": p.view_count
                }

        result = {
            "related": ordered_slugs[:4],
            "posts": posts_details
        }

        # Cache result for 1 hour
        cache.set(cache_key, result, 3600)
        return JsonResponse(result)
