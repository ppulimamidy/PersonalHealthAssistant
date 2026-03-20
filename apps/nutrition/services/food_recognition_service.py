# pylint: disable=wrong-import-order,unused-import,too-many-locals,import-outside-toplevel,broad-except,invalid-name,logging-fstring-interpolation,too-many-branches,protected-access,f-string-without-interpolation,duplicate-code
import io
import os
import uuid
import base64
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp
from PIL import Image

# Remove the circular import - we'll use lazy imports instead
# from apps.nutrition.services.nutrition_service import NutritionService

logger = logging.getLogger(__name__)


class FoodRecognitionService:
    """
    Service for food recognition and portion estimation from images.
    Integrates with multiple AI vision APIs for robust food detection.
    Now includes comprehensive calorie and macronutrient calculations.
    """

    def __init__(self):
        # API Keys
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.google_vision_api_key = os.getenv("GOOGLE_VISION_API_KEY")
        self.azure_vision_api_key = os.getenv("AZURE_VISION_API_KEY")
        self.azure_vision_endpoint = os.getenv("AZURE_VISION_ENDPOINT")

        # Service availability flags
        self.openai_available = bool(self.openai_api_key)
        self.anthropic_available = bool(self.anthropic_api_key)
        self.google_available = bool(self.google_vision_api_key)
        self.azure_available = bool(
            self.azure_vision_api_key and self.azure_vision_endpoint
        )

        # Don't initialize nutrition service here to avoid circular import
        self.nutrition_service = None

    def _get_nutrition_service(self):
        """Lazy initialization of nutrition service to avoid circular imports."""
        if self.nutrition_service is None:
            from apps.nutrition.services.nutrition_service import NutritionService

            self.nutrition_service = NutritionService()
        return self.nutrition_service

    async def recognize_food(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main method for food recognition from image with comprehensive analysis.
        Now includes calorie and macronutrient calculations.
        """
        import time

        start_time = time.time()

        user_id_raw = request_data.get("user_id")
        if not isinstance(user_id_raw, str) or not user_id_raw.strip():
            raise ValueError("user_id is required")
        user_id: str = user_id_raw

        image_data_raw = request_data.get("image_data")
        if not isinstance(image_data_raw, (bytes, bytearray)):
            raise ValueError("image_data must be bytes")
        image_data: bytes = bytes(image_data_raw)
        models_to_use = request_data.get("models_to_use", ["google_vision"])
        enable_portion_estimation = request_data.get("enable_portion_estimation", True)
        enable_nutrition_lookup = request_data.get("enable_nutrition_lookup", True)

        try:
            # Recognize foods in image
            recognized_foods = await self.recognize_foods_in_image(image_data, user_id)
            used_mock = any(
                bool(item.get("is_mock_result")) for item in (recognized_foods or [])
            )

            # Estimate portion sizes if enabled
            if enable_portion_estimation:
                recognized_foods = await self.estimate_portion_size(
                    image_data, recognized_foods
                )

            # Calculate nutrition data if enabled
            total_calories = 0.0
            total_protein = 0.0
            total_carbs = 0.0
            total_fat = 0.0

            if enable_nutrition_lookup and recognized_foods:
                nutrition_results = await self._calculate_nutrition_for_foods(
                    recognized_foods
                )

                # Update recognized foods with nutrition data
                for i, food_item in enumerate(recognized_foods):
                    if i < len(nutrition_results):
                        food_item.update(nutrition_results[i])

                # Calculate totals
                total_calories = sum(
                    item.get("calories", 0) for item in recognized_foods
                )
                total_protein = sum(
                    item.get("protein_g", 0) for item in recognized_foods
                )
                total_carbs = sum(item.get("carbs_g", 0) for item in recognized_foods)
                total_fat = sum(item.get("fat_g", 0) for item in recognized_foods)

            # Calculate processing time
            processing_time = time.time() - start_time

            # Calculate overall confidence (average of all food items)
            overall_confidence = 0.0
            if recognized_foods:
                overall_confidence = sum(
                    item.get("confidence", 0) for item in recognized_foods
                ) / len(recognized_foods)

            # Generate recognition ID
            recognition_id = str(uuid.uuid4())

            # Create response that matches the expected Pydantic model
            warnings: List[str] = []
            if used_mock:
                warnings.append(
                    "Food recognition fell back to a default demo response. "
                    "At least one vision provider is failing or not configured (e.g., OpenAI quota, missing Google/Azure keys)."
                )

            response = {
                "request_id": recognition_id,
                "user_id": user_id,
                "recognized_foods": recognized_foods,
                "total_calories": round(total_calories, 1),
                "total_protein": round(total_protein, 1),
                "total_carbs": round(total_carbs, 1),
                "total_fat": round(total_fat, 1),
                "processing_time": processing_time,
                "models_used": models_to_use,
                "overall_confidence": overall_confidence,
                "image_quality_score": 0.8,  # TODO: Calculate actual quality score
                "suggestions": self._generate_nutrition_suggestions(
                    total_calories, total_protein, total_carbs, total_fat
                ),
                "warnings": warnings
                + self._generate_nutrition_warnings(recognized_foods),
                "detected_cuisine": request_data.get("cuisine_hint"),
                "detected_region": request_data.get("region_hint"),
                "timestamp": datetime.utcnow().isoformat(),
                "image_url": None,  # TODO: Store image and return URL
            }

            return response

        except Exception as e:
            logger.error(f"Food recognition failed: {e}")
            raise

    async def recognize_food_batch(
        self, batch_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process multiple food images in batch for recognition and analysis.
        """
        user_id = batch_request.get("user_id")
        images = batch_request.get("images", [])

        results = []
        for image_data in images:
            try:
                result = await self.recognize_food(
                    {
                        "user_id": user_id,
                        "image_data": image_data.get("image_data"),
                        "image_format": image_data.get("image_format", "jpeg"),
                        "models_to_use": batch_request.get(
                            "models_to_use", ["google_vision"]
                        ),
                        "enable_portion_estimation": batch_request.get(
                            "enable_portion_estimation", True
                        ),
                        "enable_nutrition_lookup": batch_request.get(
                            "enable_nutrition_lookup", True
                        ),
                    }
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process image in batch: {e}")
                results.append({"error": str(e)})

        return {
            "batch_id": str(uuid.uuid4()),
            "user_id": user_id,
            "total_images": len(images),
            "successful_results": len([r for r in results if "error" not in r]),
            "results": results,
        }

    async def correct_recognition(
        self, recognition_id: str, user_id: str, corrections: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply user corrections to recognition results and learn from them.
        """
        try:
            # TODO: Retrieve original recognition result from database
            original_result: Dict[str, Any] = {"recognized_foods": []}  # Placeholder

            # Apply corrections
            corrected_foods = []
            for food_item in original_result.get("recognized_foods", []):
                food_name = food_item.get("name")
                if food_name in corrections:
                    correction = corrections[food_name]
                    corrected_foods.append(
                        {
                            **food_item,
                            "corrected_name": correction.get("correct_name"),
                            "corrected_portion": correction.get("corrected_portion"),
                            "user_confidence": correction.get("confidence", 1.0),
                        }
                    )
                else:
                    corrected_foods.append(food_item)

            # Learn from corrections
            await self.learn_from_user_correction(
                user_id,
                {
                    "recognition_id": recognition_id,
                    "corrections": corrections,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

            return {
                "recognition_id": recognition_id,
                "user_id": user_id,
                "corrected_foods": corrected_foods,
                "corrections_applied": len(corrections),
            }

        except Exception as e:
            logger.error(f"Failed to apply corrections: {e}")
            raise

    async def get_recognition_history(
        self, user_id: str, limit: int = 20, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get user's food recognition history.
        """
        # TODO: Query database for user's recognition history
        return []

    async def get_recognition_statistics(
        self, user_id: str, timeframe: str = "30_days"
    ) -> Dict[str, Any]:
        """
        Get recognition statistics for a user over a timeframe.
        """
        # TODO: Calculate statistics from database
        return {
            "user_id": user_id,
            "timeframe": timeframe,
            "total_recognitions": 0,
            "accuracy_rate": 0.85,
            "most_recognized_foods": [],
            "average_confidence": 0.78,
        }

    async def estimate_single_portion_size(
        self, food_name: str, image_data: bytes, reference_object: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Estimate portion size for a specific food item.
        """
        try:
            # Use AI for portion estimation
            if self.openai_available:
                try:
                    items = await self._estimate_portion_with_openai(
                        image_data, [{"name": food_name}]
                    )
                    if items:
                        portion_g = int(items[0].get("portion_g", 100) or 100)
                        return {
                            "portion_g": portion_g,
                            "confidence": 0.7,
                            "method": "openai",
                        }
                except Exception as e:
                    logger.warning(f"OpenAI portion estimation failed: {e}")

            # Fallback to heuristic estimation
            items = self._estimate_portion_heuristic(
                [{"name": food_name, "category": "other"}]
            )
            portion_g = int(items[0].get("portion_g", 100) or 100) if items else 100
            return {"portion_g": portion_g, "confidence": 0.4, "method": "heuristic"}

        except Exception as e:
            logger.error(f"Portion estimation failed: {e}")
            return {"portion_g": 100, "confidence": 0.5}

    async def get_supported_models(self) -> List[Dict[str, Any]]:
        """
        Get list of supported recognition models.
        """
        models = []

        if self.openai_available:
            models.append(
                {
                    "name": "openai_vision",
                    "display_name": "OpenAI Vision",
                    "description": "Advanced AI vision model for food recognition",
                    "accuracy": 0.95,
                    "speed": "medium",
                    "cost": "high",
                }
            )

        if self.google_available:
            models.append(
                {
                    "name": "google_vision",
                    "display_name": "Google Vision AI",
                    "description": "Google's computer vision API",
                    "accuracy": 0.90,
                    "speed": "fast",
                    "cost": "medium",
                }
            )

        if self.azure_available:
            models.append(
                {
                    "name": "azure_vision",
                    "display_name": "Azure Computer Vision",
                    "description": "Microsoft's computer vision service",
                    "accuracy": 0.88,
                    "speed": "fast",
                    "cost": "medium",
                }
            )

        return models

    async def get_model_performance(self) -> Dict[str, Any]:
        """
        Get performance metrics for recognition models.
        """
        # TODO: Calculate actual performance metrics from database
        return {
            "overall_accuracy": 0.92,
            "model_performance": {
                "openai_vision": {"accuracy": 0.95, "speed_ms": 1500},
                "google_vision": {"accuracy": 0.90, "speed_ms": 800},
                "azure_vision": {"accuracy": 0.88, "speed_ms": 900},
            },
            "user_satisfaction": 0.87,
        }

    async def improve_recognition_model(
        self, training_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Submit training data to improve recognition models.
        """
        try:
            # TODO: Store training data for model improvement
            # TODO: Trigger model retraining pipeline

            return {
                "status": "training_data_received",
                "message": "Training data has been submitted for model improvement",
                "estimated_improvement_time": "2-4 weeks",
            }

        except Exception as e:
            logger.error(f"Failed to submit training data: {e}")
            raise

    async def recognize_foods_in_image(
        self, image_bytes: bytes, user_id: str
    ) -> List[Dict[str, Any]]:
        """
        Recognize foods in an image using multiple AI vision APIs.
        Returns a list of detected food items with confidence scores.
        Priority: Anthropic → OpenAI → Google → Azure → mock fallback.
        """
        try:
            # Try Anthropic Claude Vision first (configured and quota available)
            if self.anthropic_available:
                try:
                    return await self._recognize_with_anthropic(image_bytes)
                except Exception as e:
                    logger.warning(f"Anthropic Vision failed: {e}")

            # Try OpenAI Vision
            if self.openai_available:
                try:
                    return await self._recognize_with_openai(image_bytes)
                except Exception as e:
                    logger.warning(f"OpenAI Vision failed: {e}")

            # Fallback to Google Vision
            if self.google_available:
                try:
                    return await self._recognize_with_google(image_bytes)
                except Exception as e:
                    logger.warning(f"Google Vision failed: {e}")

            # Fallback to Azure Vision
            if self.azure_available:
                try:
                    return await self._recognize_with_azure(image_bytes)
                except Exception as e:
                    logger.warning(f"Azure Vision failed: {e}")

            # If all APIs fail, return mock results
            logger.warning("All vision APIs failed, using mock results")
            return self._get_mock_recognition_results()

        except Exception as e:
            logger.error(f"Food recognition failed: {e}")
            return self._get_mock_recognition_results()

    def _image_media_type(self, image_bytes: bytes) -> str:
        """Detect image MIME type from bytes using PIL."""
        try:
            img = Image.open(io.BytesIO(image_bytes))
            fmt = (img.format or "JPEG").upper()
            return {
                "JPEG": "image/jpeg",
                "PNG": "image/png",
                "GIF": "image/gif",
                "WEBP": "image/webp",
            }.get(fmt, "image/jpeg")
        except Exception:
            return "image/jpeg"

    def _compress_for_api(
        self, image_bytes: bytes, max_bytes: int = 4_500_000
    ) -> bytes:
        """Compress/resize image so it stays under max_bytes (default 4.5 MB).

        Anthropic's hard limit is 5 MB per image.  Large phone photos routinely
        exceed that, so we resize them down before encoding to base64.
        """
        if len(image_bytes) <= max_bytes:
            return image_bytes
        try:
            img = Image.open(io.BytesIO(image_bytes))
            # Convert to RGB so we can always save as JPEG
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            quality = 85
            scale = 1.0
            while True:
                buf = io.BytesIO()
                w = int(img.width * scale)
                h = int(img.height * scale)
                out = img.resize((w, h), Image.LANCZOS) if scale < 1.0 else img
                out.save(buf, format="JPEG", quality=quality, optimize=True)
                compressed = buf.getvalue()
                if len(compressed) <= max_bytes:
                    logger.info(
                        f"Compressed image {len(image_bytes) // 1024}KB → "
                        f"{len(compressed) // 1024}KB (scale={scale:.2f}, q={quality})"
                    )
                    return compressed
                # Reduce quality first, then resolution
                if quality > 60:
                    quality -= 10
                else:
                    scale *= 0.75
                if scale < 0.1:
                    # Give up and return whatever we have
                    return compressed
        except Exception as exc:
            logger.warning(f"Image compression failed: {exc} — sending original")
            return image_bytes

    async def _recognize_with_anthropic(
        self, image_bytes: bytes
    ) -> List[Dict[str, Any]]:
        """Recognize foods using Anthropic Claude Vision API."""
        import anthropic
        import json

        # base64 encoding adds ~33% overhead; Anthropic limit is 5 MB base64
        # so raw bytes must be ≤ 3.5 MB to stay safely under 5 MB after encoding
        image_bytes = self._compress_for_api(image_bytes, max_bytes=3_500_000)
        client = anthropic.AsyncAnthropic(api_key=self.anthropic_api_key)
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        media_type = self._image_media_type(image_bytes)

        prompt = """Analyze this food image and identify all food items present.
Return ONLY a valid JSON array with each food item containing:
- name: a specific, descriptive food name (string). Include visual details:
  cooking method (grilled, fried, steamed), ripeness/color, and preparation style.
  Examples: "ripe banana", "fried chicken nuggets", "steamed white rice", "sliced whole wheat bread"
- quantity: how many of this item are visible (number, e.g. 2 for two bananas, 4 for four nuggets, 1 for a plate of rice)
- unit: the most natural unit for this food (string). Use: "pieces" (bananas, eggs), "nuggets" (chicken nuggets),
  "slices" (bread, pizza), "cups" (rice, soup), "bowl" (soup, oatmeal), "patty" (burgers),
  "fillet" (fish), "wing" (chicken wings), "strip" (bacon), "serving" (mixed dishes), or "g" (grams) for loose items
- confidence: confidence score (number 0-1)
- description: brief description of what you see (string)
- category: food category (one of: protein, vegetable, grain, fruit, dairy, beverage, condiment, other)

IMPORTANT: Count discrete items carefully. If you see 2 bananas, return quantity 2. If you see 4 nuggets, return quantity 4.
For plated foods like rice or pasta, estimate in cups or servings.
Identify every distinct food item visible. Return the JSON array only, no markdown fences or extra text.

Example:
[{"name": "ripe banana", "quantity": 2, "unit": "pieces", "confidence": 0.95, "description": "Two ripe yellow bananas", "category": "fruit"}, {"name": "fried chicken nuggets", "quantity": 4, "unit": "nuggets", "confidence": 0.90, "description": "Four golden-brown breaded chicken nuggets", "category": "protein"}]"""

        result = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_base64,
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        )

        content = result.content[0].text.strip()
        # Strip markdown fences if present
        if "```json" in content:
            content = content[
                content.find("```json") + 7 : content.rfind("```")
            ].strip()
        elif "```" in content:
            content = content[content.find("```") + 3 : content.rfind("```")].strip()

        food_data = json.loads(content)
        food_items = []
        if isinstance(food_data, list):
            for item in food_data:
                if isinstance(item, dict):
                    entry = {
                        "name": item.get("name", "unknown"),
                        "confidence": item.get("confidence", 0.8),
                        "description": item.get("description", ""),
                        "category": item.get("category", "other"),
                        "model_used": "anthropic_vision",
                    }
                    # Carry forward quantity/unit from recognition step
                    if item.get("quantity") is not None:
                        entry["quantity"] = float(item["quantity"])
                    if item.get("unit"):
                        entry["unit"] = item["unit"]
                    food_items.append(entry)

        if food_items:
            logger.info(f"Anthropic Vision recognized {len(food_items)} food items")
            return food_items

        logger.warning("Anthropic Vision returned empty food items")
        return self._get_mock_recognition_results()

    async def _recognize_with_openai(self, image_bytes: bytes) -> List[Dict[str, Any]]:
        """Recognize foods using OpenAI Vision API."""
        import openai

        client = openai.AsyncOpenAI(api_key=self.openai_api_key)

        # Convert image to base64
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        prompt = """Analyze this food image and identify all food items present.
Return ONLY a valid JSON array with each food item containing:
- name: a specific, descriptive food name. Include cooking method, ripeness, or preparation details.
  Examples: "ripe banana", "fried chicken nuggets", "steamed white rice"
- quantity: how many of this item are visible (number, e.g. 2 for two bananas, 4 for four nuggets)
- unit: the most natural unit (pieces, nuggets, slices, cups, bowl, patty, fillet, wing, strip, serving, or g)
- confidence: confidence score (number 0-1)
- description: brief description of what you see
- category: food category (protein, vegetable, grain, fruit, dairy, beverage, condiment, or other)

IMPORTANT: Count discrete items carefully. If you see 2 bananas return quantity 2. For plated foods estimate in cups or servings.
Return the JSON array directly without any markdown formatting or additional text.

Example:
[{"name": "ripe banana", "quantity": 2, "unit": "pieces", "confidence": 0.95, "description": "Two ripe yellow bananas", "category": "fruit"}]"""

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            },
                        },
                    ],
                }
            ],
            max_tokens=1000,
        )

        # Parse the response
        content = response.choices[0].message.content

        try:
            # Try to extract JSON from the response
            # OpenAI might wrap JSON in markdown code blocks
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                json_content = content[json_start:json_end].strip()
            elif "```" in content:
                json_start = content.find("```") + 3
                json_end = content.find("```", json_start)
                json_content = content[json_start:json_end].strip()
            else:
                json_content = content.strip()

            # Parse the JSON response
            import json

            food_data = json.loads(json_content)

            # Extract food items from the parsed response
            food_items = []
            items_list = []
            if isinstance(food_data, list):
                items_list = food_data
            elif isinstance(food_data, dict) and "foods" in food_data:
                items_list = food_data["foods"]

            for item in items_list:
                if isinstance(item, dict):
                    entry = {
                        "name": item.get("name", "unknown"),
                        "confidence": item.get("confidence", 0.5),
                        "description": item.get("description", ""),
                        "category": item.get("category", "other"),
                        "model_used": "openai_vision",
                    }
                    if item.get("quantity") is not None:
                        entry["quantity"] = float(item["quantity"])
                    if item.get("unit"):
                        entry["unit"] = item["unit"]
                    food_items.append(entry)

            if food_items:
                logger.info(
                    f"OpenAI Vision successfully recognized {len(food_items)} food items"
                )
                return food_items
            else:
                logger.warning(
                    "OpenAI Vision returned empty food items, falling back to mock"
                )
                return self._get_mock_recognition_results()

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning(f"Failed to parse OpenAI Vision response: {e}")
            logger.debug(f"Raw OpenAI response: {content}")
            return self._get_mock_recognition_results()

    async def _recognize_with_google(self, image_bytes: bytes) -> List[Dict[str, Any]]:
        """Recognize foods using Google Vision API."""
        async with aiohttp.ClientSession() as session:
            # Convert image to base64
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")

            url = f"https://vision.googleapis.com/v1/images:annotate?key={self.google_vision_api_key}"

            payload = {
                "requests": [
                    {
                        "image": {"content": image_base64},
                        "features": [
                            {"type": "LABEL_DETECTION", "maxResults": 20},
                            {"type": "OBJECT_LOCALIZATION", "maxResults": 10},
                        ],
                    }
                ]
            }

            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_google_vision_response(data)
                else:
                    raise Exception(f"Google Vision API error: {response.status}")

    async def _recognize_with_azure(self, image_bytes: bytes) -> List[Dict[str, Any]]:
        """Recognize foods using Azure Computer Vision API."""
        async with aiohttp.ClientSession() as session:
            # Convert image to base64
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")

            url = f"{self.azure_vision_endpoint}/vision/v3.2/analyze?visualFeatures=Tags,Objects&language=en"

            headers = {
                "Content-Type": "application/octet-stream",
                "Ocp-Apim-Subscription-Key": self.azure_vision_api_key,
            }

            async with session.post(url, data=image_bytes, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_azure_vision_response(data)
                else:
                    raise Exception(f"Azure Vision API error: {response.status}")

    def _parse_google_vision_response(
        self, data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Parse Google Vision API response to extract food items."""
        food_items = []

        # Extract labels
        if "responses" in data and data["responses"]:
            annotations = data["responses"][0].get("labelAnnotations", [])
            for annotation in annotations:
                description = annotation.get("description", "").lower()
                confidence = annotation.get("score", 0)

                # Filter for food-related labels
                if self._is_food_item(description):
                    food_items.append(
                        {
                            "name": description,
                            "confidence": confidence,
                            "description": f"Detected {description}",
                            "category": self._categorize_food(description),
                        }
                    )

        return food_items[:10]  # Limit to top 10 results

    def _parse_azure_vision_response(
        self, data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Parse Azure Vision API response to extract food items."""
        food_items = []

        # Extract tags
        tags = data.get("tags", [])
        for tag in tags:
            name = tag.get("name", "").lower()
            confidence = tag.get("confidence", 0)

            if self._is_food_item(name):
                food_items.append(
                    {
                        "name": name,
                        "confidence": confidence,
                        "description": f"Detected {name}",
                        "category": self._categorize_food(name),
                    }
                )

        return food_items[:10]  # Limit to top 10 results

    def _is_food_item(self, item_name: str) -> bool:
        """Check if an item is food-related."""
        food_keywords = [
            "food",
            "meal",
            "dish",
            "cuisine",
            "cooking",
            "recipe",
            "rice",
            "chicken",
            "beef",
            "pork",
            "fish",
            "vegetable",
            "fruit",
            "bread",
            "pasta",
            "soup",
            "salad",
            "dessert",
            "drink",
            "beverage",
            "sauce",
            "spice",
            "herb",
        ]
        return any(keyword in item_name for keyword in food_keywords)

    def _categorize_food(self, food_name: str) -> str:
        """Categorize food into basic categories."""
        categories = {
            "protein": ["chicken", "beef", "pork", "fish", "meat", "egg", "tofu"],
            "vegetable": ["broccoli", "carrot", "lettuce", "tomato", "onion", "pepper"],
            "grain": ["rice", "bread", "pasta", "noodle", "quinoa", "oat"],
            "fruit": ["apple", "banana", "orange", "grape", "berry"],
            "dairy": ["milk", "cheese", "yogurt", "cream", "butter"],
        }

        for category, keywords in categories.items():
            if any(keyword in food_name for keyword in keywords):
                return category

        return "other"

    def _get_mock_recognition_results(self) -> List[Dict[str, Any]]:
        """Return mock recognition results for fallback."""
        return [
            {
                "name": "rice",
                "confidence": 0.95,
                "description": "White rice",
                "category": "grain",
                "model_used": "google_vision",
                "is_mock_result": True,
            },
            {
                "name": "chicken",
                "confidence": 0.90,
                "description": "Grilled chicken",
                "category": "protein",
                "model_used": "google_vision",
                "is_mock_result": True,
            },
            {
                "name": "broccoli",
                "confidence": 0.85,
                "description": "Steamed broccoli",
                "category": "vegetable",
                "model_used": "google_vision",
                "is_mock_result": True,
            },
        ]

    async def estimate_portion_size(
        self, image_bytes: bytes, food_items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Estimate portion sizes for detected food items using AI or heuristics.
        Returns food items with estimated portion sizes (grams).
        Priority: Anthropic → OpenAI → heuristic fallback.
        """
        try:
            # Use Anthropic for portion estimation
            if self.anthropic_available:
                try:
                    return await self._estimate_portion_with_anthropic(
                        image_bytes, food_items
                    )
                except Exception as e:
                    logger.warning(f"Anthropic portion estimation failed: {e}")

            # Fallback to OpenAI
            if self.openai_available:
                try:
                    return await self._estimate_portion_with_openai(
                        image_bytes, food_items
                    )
                except Exception as e:
                    logger.warning(f"OpenAI portion estimation failed: {e}")

            # Fallback to heuristic estimation
            return self._estimate_portion_heuristic(food_items)

        except Exception as e:
            logger.error(f"Portion estimation failed: {e}")
            return self._estimate_portion_heuristic(food_items)

    async def _estimate_portion_with_anthropic(
        self, image_bytes: bytes, food_items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Estimate portions using Anthropic Claude Vision API."""
        import anthropic
        import json

        image_bytes = self._compress_for_api(image_bytes, max_bytes=3_500_000)
        client = anthropic.AsyncAnthropic(api_key=self.anthropic_api_key)
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        media_type = self._image_media_type(image_bytes)
        food_names = [item["name"] for item in food_items]

        prompt = f"""Analyze this food image and estimate the portion sizes for these food items: {', '.join(food_names)}.

Consider:
- Visual size relative to common objects (plate, spoon, fork, etc.)
- Typical serving sizes for each food
- Density and volume of the food visible
- Count discrete items when applicable (e.g. 2 bananas, 6 nuggets, 3 slices)

Return ONLY a JSON object where each key is the food name and the value is an object with:
- "quantity": numeric amount (e.g. 2, 1.5, 6)
- "unit": the most natural unit for this food. Use common household units when appropriate:
  piece/pieces (bananas, eggs, cookies), slice/slices (bread, pizza, cheese),
  nuggets (chicken nuggets), cups (rice, soup, cereal), bowl (soup, oatmeal),
  scoop/scoops (ice cream, protein powder), handful (nuts, chips),
  wing (chicken wings), strip (bacon), patty (burgers), fillet (fish),
  serving, or g (grams) for foods where weight is most natural (meat portions, etc.)
- "grams": estimated weight in grams

Example: {{"banana": {{"quantity": 2, "unit": "pieces", "grams": 240}}, "grilled salmon": {{"quantity": 1, "unit": "fillet", "grams": 180}}, "steamed rice": {{"quantity": 1, "unit": "cups", "grams": 185}}, "chicken nuggets": {{"quantity": 6, "unit": "nuggets", "grams": 108}}}}"""

        result = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_base64,
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        )

        content = result.content[0].text.strip()
        if "```json" in content:
            content = content[
                content.find("```json") + 7 : content.rfind("```")
            ].strip()
        elif "```" in content:
            content = content[content.find("```") + 3 : content.rfind("```")].strip()

        parsed = json.loads(content)
        if not isinstance(parsed, dict):
            return self._estimate_portion_heuristic(food_items)

        updated: List[Dict[str, Any]] = []
        for item in food_items:
            name = (item.get("name") or "").strip()
            entry = parsed.get(name) or parsed.get(name.lower())

            # Support both new {quantity, unit, grams} format and legacy int format
            if isinstance(entry, dict):
                g_val = int(float(entry.get("grams", 0)))
                quantity = float(entry.get("quantity", 1))
                unit = entry.get("unit", "g")
            elif entry is not None:
                try:
                    g_val = int(float(entry))
                except Exception:
                    g_val = 0
                quantity = g_val
                unit = "g"
            else:
                # No match from portion estimation — fall back to recognition-step values
                recog_qty = item.get("quantity", 1)
                recog_unit = item.get("unit", "g")
                g_val = 0
                quantity = float(recog_qty) if recog_qty else 0
                unit = recog_unit or "g"

            if not g_val or g_val <= 0:
                # Still carry recognition-step quantity/unit even without gram estimate
                if item.get("quantity") or item.get("unit"):
                    updated.append(
                        {
                            **item,
                            "quantity": item.get("quantity", 1),
                            "unit": item.get("unit", "serving"),
                        }
                    )
                else:
                    updated.append(item)
                continue

            updated.append(
                {
                    **item,
                    "portion_g": g_val,
                    "quantity": quantity,
                    "unit": unit,
                    "portion_estimate": {
                        "food_name": name or item.get("name", "unknown"),
                        "estimated_quantity": quantity,
                        "unit": unit,
                        "grams": g_val,
                        "confidence": 0.75,
                    },
                    "estimation_method": "anthropic",
                }
            )

        return updated

    async def _estimate_portion_with_openai(
        self, image_bytes: bytes, food_items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Estimate portions using OpenAI Vision API."""
        import openai

        client = openai.AsyncOpenAI(api_key=self.openai_api_key)

        # Convert image to base64
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        food_names = [item["name"] for item in food_items]
        prompt = f"""
        Analyze this food image and estimate the portion sizes for these food items: {', '.join(food_names)}.

        Consider:
        - Visual size relative to common objects (spoon, plate, etc.)
        - Typical serving sizes
        - Density of the food
        - Count discrete items when applicable (e.g. 2 bananas, 6 nuggets, 3 slices)

        Return a JSON object where each key is the food name and the value is an object with:
        - "quantity": numeric amount (e.g. 2, 1.5, 6)
        - "unit": the most natural unit for this food (pieces, slices, nuggets, cups, bowl, scoop, handful, wing, strip, patty, fillet, serving, or g for grams)
        - "grams": estimated weight in grams

        Example: {{"banana": {{"quantity": 2, "unit": "pieces", "grams": 240}}, "rice": {{"quantity": 1, "unit": "cups", "grams": 185}}, "chicken nuggets": {{"quantity": 6, "unit": "nuggets", "grams": 108}}}}
        """

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            },
                        },
                    ],
                }
            ],
            max_tokens=500,
        )

        content = response.choices[0].message.content or ""
        try:
            import json

            # Extract JSON object if wrapped in code fences
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                json_content = content[json_start:json_end].strip()
            elif "```" in content:
                json_start = content.find("```") + 3
                json_end = content.find("```", json_start)
                json_content = content[json_start:json_end].strip()
            else:
                json_content = content.strip()

            parsed = json.loads(json_content) if json_content else {}
            if not isinstance(parsed, dict):
                return self._estimate_portion_heuristic(food_items)

            updated: List[Dict[str, Any]] = []
            for item in food_items:
                name = (item.get("name") or "").strip()
                entry = parsed.get(name)
                if entry is None:
                    entry = parsed.get(name.lower())

                # Support both new {quantity, unit, grams} format and legacy int format
                if isinstance(entry, dict):
                    g_val = int(float(entry.get("grams", 0)))
                    quantity = float(entry.get("quantity", 1))
                    unit = entry.get("unit", "g")
                elif entry is not None:
                    try:
                        g_val = int(float(entry))
                    except Exception:
                        g_val = 0
                    quantity = g_val
                    unit = "g"
                else:
                    g_val = 0
                    quantity = 0
                    unit = "g"

                if g_val is None or g_val <= 0:
                    updated.append(item)
                    continue

                updated.append(
                    {
                        **item,
                        "portion_g": g_val,
                        "quantity": quantity,
                        "unit": unit,
                        "portion_estimate": {
                            "food_name": name or (item.get("name") or "unknown"),
                            "estimated_quantity": quantity,
                            "unit": unit,
                            "grams": g_val,
                            "confidence": 0.7,
                        },
                        "estimation_method": "openai",
                    }
                )

            return updated
        except Exception as e:
            logger.warning(f"Failed to parse OpenAI portion JSON: {e}")
            return self._estimate_portion_heuristic(food_items)

    def _estimate_portion_heuristic(
        self, food_items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Estimate portion sizes using heuristic rules when AI estimation is not available.
        Now returns natural units (pieces, slices, cups, etc.) when appropriate.
        """
        estimated_items = []

        # Map food keywords to natural units: (grams, quantity, unit)
        NATURAL_UNITS = {
            "banana": (120, 1, "piece"),
            "apple": (180, 1, "piece"),
            "orange": (130, 1, "piece"),
            "egg": (50, 1, "piece"),
            "cookie": (35, 1, "piece"),
            "donut": (60, 1, "piece"),
            "muffin": (115, 1, "piece"),
            "pancake": (75, 1, "piece"),
            "waffle": (75, 1, "piece"),
            "tortilla": (50, 1, "piece"),
            "nugget": (18, 1, "nugget"),
            "wing": (30, 1, "wing"),
            "pizza": (110, 1, "slice"),
            "bread": (30, 1, "slice"),
            "toast": (30, 1, "slice"),
            "cheese slice": (20, 1, "slice"),
            "bacon": (8, 1, "strip"),
            "rice": (185, 1, "cups"),
            "cereal": (30, 1, "bowl"),
            "oatmeal": (235, 1, "bowl"),
            "soup": (400, 1, "bowl"),
            "pasta": (140, 1, "cups"),
            "ice cream": (65, 1, "scoop"),
            "protein powder": (30, 1, "scoop"),
            "yogurt": (245, 1, "cups"),
            "milk": (244, 1, "cups"),
            "nuts": (30, 1, "handful"),
            "almonds": (30, 1, "handful"),
            "chips": (25, 1, "handful"),
            "burger": (115, 1, "patty"),
            "salmon": (170, 1, "fillet"),
            "steak": (225, 1, "piece"),
            "sausage": (45, 1, "piece"),
            "granola bar": (40, 1, "bar"),
            "protein bar": (60, 1, "bar"),
        }

        for food_item in food_items:
            food_name = food_item.get("name", "").lower()
            category = food_item.get("category", "other")

            # Check for natural unit match
            matched = False
            for keyword, (grams, qty, unit) in NATURAL_UNITS.items():
                if keyword in food_name:
                    estimated_items.append(
                        {
                            **food_item,
                            "portion_g": grams,
                            "quantity": qty,
                            "unit": unit,
                            "portion_estimate": {
                                "food_name": (food_item.get("name") or "").strip()
                                or "unknown",
                                "estimated_quantity": qty,
                                "unit": unit,
                                "grams": grams,
                                "confidence": 0.4,
                            },
                            "confidence": 0.7,
                            "estimation_method": "heuristic",
                        }
                    )
                    matched = True
                    break

            if matched:
                continue

            # Fallback: category-based grams
            default_portion = 100
            if category == "grains":
                default_portion = 150
            elif category == "protein" or "chicken" in food_name or "meat" in food_name:
                default_portion = 120
            elif category == "vegetables":
                default_portion = 80
            elif category == "fruits":
                default_portion = 120
            elif category == "dairy":
                default_portion = 100
            elif category == "nuts":
                default_portion = 30
            elif category == "oils":
                default_portion = 15

            if "sandwich" in food_name:
                default_portion = 200
            elif "salad" in food_name:
                default_portion = 100

            estimated_items.append(
                {
                    **food_item,
                    "portion_g": default_portion,
                    "quantity": default_portion,
                    "unit": "g",
                    "portion_estimate": {
                        "food_name": (food_item.get("name") or "").strip() or "unknown",
                        "estimated_quantity": default_portion,
                        "unit": "g",
                        "grams": default_portion,
                        "confidence": 0.4,
                    },
                    "confidence": 0.7,
                    "estimation_method": "heuristic",
                }
            )

        return estimated_items

    async def _calculate_nutrition_for_foods(
        self, recognized_foods: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Calculate nutrition data for recognized food items.
        """
        nutrition_results = []

        for food_item in recognized_foods:
            try:
                food_name = food_item.get("name", "")
                portion_g = food_item.get("portion_g", 100)

                # Create food item data for nutrition service
                food_data = {
                    "name": food_name,
                    "portion_g": portion_g,
                    "category": food_item.get("category", "other"),
                }

                # Get nutrition data from nutrition service
                nutrition_data = (
                    await self._get_nutrition_service()._fetch_nutrition_data(food_data)
                )

                # Add nutrition data to food item
                food_item.update(nutrition_data)
                nutrition_results.append(food_item)

            except Exception as e:
                logger.warning(
                    f"Failed to calculate nutrition for {food_item.get('name', 'unknown')}: {e}"
                )
                # Add default nutrition data
                food_item.update(
                    {
                        "calories": 0,
                        "protein_g": 0.0,
                        "carbs_g": 0.0,
                        "fat_g": 0.0,
                        "fiber_g": 0.0,
                        "sodium_mg": 0,
                        "sugar_g": 0.0,
                    }
                )
                nutrition_results.append(food_item)

        return nutrition_results

    def _generate_nutrition_suggestions(
        self,
        total_calories: float,
        total_protein: float,
        total_carbs: float,
        total_fat: float,
    ) -> List[str]:
        """
        Generate nutrition suggestions based on calculated values.
        """
        suggestions = []

        # Calorie suggestions
        if total_calories < 200:
            suggestions.append(
                "This appears to be a light meal. Consider adding more nutrient-dense foods."
            )
        elif total_calories > 800:
            suggestions.append(
                "This is a high-calorie meal. Consider portion control for weight management."
            )

        # Protein suggestions
        if total_protein < 10:
            suggestions.append(
                "Low protein content. Consider adding lean protein sources."
            )
        elif total_protein > 50:
            suggestions.append(
                "High protein meal. Great for muscle building and satiety."
            )

        # Carbohydrate suggestions
        if total_carbs < 20:
            suggestions.append(
                "Low carbohydrate content. May need more energy sources."
            )
        elif total_carbs > 100:
            suggestions.append(
                "High carbohydrate content. Consider balance with protein and fats."
            )

        # Fat suggestions
        if total_fat < 5:
            suggestions.append(
                "Low fat content. Consider healthy fats for nutrient absorption."
            )
        elif total_fat > 30:
            suggestions.append("High fat content. Consider reducing for heart health.")

        # Balanced meal suggestions
        if (
            200 <= total_calories <= 600
            and 15 <= total_protein <= 30
            and 20 <= total_carbs <= 80
            and 5 <= total_fat <= 25
        ):
            suggestions.append(
                "Well-balanced meal with good macronutrient distribution!"
            )

        return suggestions

    def _generate_nutrition_warnings(
        self, recognized_foods: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Generate nutrition warnings based on recognized foods.
        """
        warnings = []

        # Check for high-sodium foods
        high_sodium_foods = [
            food for food in recognized_foods if food.get("sodium_mg", 0) > 500
        ]
        if high_sodium_foods:
            warnings.append(
                f"High sodium content detected in {len(high_sodium_foods)} food item(s)."
            )

        # Check for high-sugar foods
        high_sugar_foods = [
            food for food in recognized_foods if food.get("sugar_g", 0) > 15
        ]
        if high_sugar_foods:
            warnings.append(
                f"High sugar content detected in {len(high_sugar_foods)} food item(s)."
            )

        # Check for processed foods
        processed_keywords = ["processed", "canned", "frozen", "packaged", "fast food"]
        processed_foods = []
        for food in recognized_foods:
            food_name = food.get("name", "").lower()
            if any(keyword in food_name for keyword in processed_keywords):
                processed_foods.append(food)

        if processed_foods:
            warnings.append(
                f"Processed foods detected. Consider whole food alternatives."
            )

        # Allergen warnings (basic implementation)
        common_allergens = [
            "nuts",
            "peanuts",
            "shellfish",
            "dairy",
            "eggs",
            "soy",
            "wheat",
            "fish",
        ]
        allergen_foods = []
        for food in recognized_foods:
            food_name = food.get("name", "").lower()
            if any(allergen in food_name for allergen in common_allergens):
                allergen_foods.append(food)

        if allergen_foods:
            warnings.append(
                f"Common allergens detected. Check ingredients if you have allergies."
            )

        return warnings

    async def learn_from_user_correction(
        self, user_id: str, correction_data: Dict[str, Any]
    ) -> None:
        """
        Update recognition model or log corrections for future improvement.
        """
        try:
            # TODO: Store correction data in database for model retraining
            # TODO: Send correction data to model training pipeline
            logger.info(f"User correction logged for user {user_id}: {correction_data}")
        except Exception as e:
            logger.error(f"Failed to log user correction: {e}")
