"""
WebSocket router for AI Reasoning Orchestrator.
Handles real-time health insights via WebSocket connections.
"""

import asyncio
import json
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from common.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


# WebSocket endpoint for real-time insights
@router.websocket("/ws/insights/{user_id}")
async def websocket_insights(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time health insights and alerts."""
    await websocket.accept()

    try:
        while True:
            # Send periodic health insights
            await asyncio.sleep(300)  # Every 5 minutes

            # For WebSocket, we'll send a simplified version
            insight_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "type": "real_time_insight",
                "message": "Health status update available",
                "priority": "normal",
            }

            await websocket.send_text(json.dumps(insight_data))

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
