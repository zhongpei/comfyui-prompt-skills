"""
Tier 2: WebSocket Event Handlers

Implements all WebSocket events for real-time communication between
Vue frontend and Opencode Core backend.
"""

from __future__ import annotations
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from flask import request
from flask_socketio import SocketIO, emit, join_room, leave_room

from ..core import (
    get_session_manager,
    get_skill_registry,
    get_opencode_client,
    get_output_formatter,
)

# Thread pool for async execution
_executor = ThreadPoolExecutor(max_workers=4)


def register_handlers(socketio: SocketIO) -> None:
    """Register all WebSocket event handlers."""
    
    @socketio.on("connect")
    def handle_connect() -> None:
        """Handle new WebSocket connection."""
        session_id = request.args.get("session_id")
        if session_id:
            # Join the room for this session
            join_room(session_id)
            
            # Get or create session
            session_manager = get_session_manager()
            session = session_manager.get_or_create_session(session_id)
            
            # Send current state
            emit("sync_state", session.to_dict())
            emit("debug_log", {
                "level": "INFO",
                "module": "SocketHandler",
                "message": f"Connected to session: {session_id}",
            })
    
    @socketio.on("disconnect")
    def handle_disconnect() -> None:
        """Handle WebSocket disconnection."""
        session_id = request.args.get("session_id")
        if session_id:
            leave_room(session_id)
    
    @socketio.on("configure")
    def handle_configure(data: dict[str, Any]) -> None:
        """
        Handle configuration update from client.
        
        Expected data:
        {
            "session_id": "...",
            "api_key": "sk-...",
            "active_skills": ["z-photo", "z-manga"],
            "model_target": "z-image-turbo"
        }
        """
        session_id = data.get("session_id")
        if not session_id:
            emit("error", {"message": "session_id is required"})
            return
        
        session_manager = get_session_manager()
        session = session_manager.update_session_config(
            session_id=session_id,
            api_key=data.get("api_key"),
            skills=data.get("active_skills"),
            model_target=data.get("model_target"),
        )
        
        if session:
            emit("debug_log", {
                "level": "INFO",
                "module": "SocketHandler",
                "message": f"Configuration updated: skills={session.skills}",
            }, room=session_id)
            emit("sync_state", session.to_dict(), room=session_id)
        else:
            emit("error", {"message": f"Session not found: {session_id}"})
    
    @socketio.on("user_message")
    def handle_user_message(data: dict[str, Any]) -> None:
        """
        Handle user message and generate prompt.
        
        Expected data:
        {
            "session_id": "...",
            "content": "用户输入的描述",
            "model_target": "z-image-turbo"
        }
        """
        session_id = data.get("session_id")
        content = data.get("content", "")
        model_target = data.get("model_target", "z-image-turbo")
        
        if not session_id:
            emit("error", {"message": "session_id is required"})
            return
        
        if not content:
            emit("error", {"message": "content is required"})
            return
        
        # Get session and update status
        session_manager = get_session_manager()
        session = session_manager.get_session(session_id)
        if not session:
            emit("error", {"message": f"Session not found: {session_id}"})
            return
        
        session_manager.set_status(session_id, "working")
        emit("status_update", {"status": "working"}, room=session_id)
        
        # Add user message to history
        session_manager.add_message(session_id, "user", content)
        
        # Execute prompt generation in thread pool
        def generate_prompt() -> None:
            try:
                emit("debug_log", {
                    "level": "INFO",
                    "module": "PromptGenerator",
                    "message": f"Generating prompt for: {content[:50]}...",
                }, room=session_id)
                
                # Get skill registry and build system prompt
                skill_registry = get_skill_registry()
                system_prompt = skill_registry.get_combined_prompt(session.skills)
                
                if system_prompt:
                    emit("debug_log", {
                        "level": "DEBUG",
                        "module": "SkillRegistry",
                        "message": f"Loaded skills: {', '.join(session.skills)}",
                    }, room=session_id)
                
                # Get OpenCode client
                opencode_client = get_opencode_client()
                
                # Ensure server is running
                if not opencode_client.ensure_server_running():
                    emit("error", {
                        "message": "OpenCode Server is not available. Please ensure 'opencode' is installed.",
                    }, room=session_id)
                    session_manager.set_status(session_id, "error")
                    return
                
                # Create or get OpenCode session
                opencode_session = opencode_client.create_session(
                    title=f"PromptSkills-{session_id[:8]}"
                )
                
                if not opencode_session:
                    emit("error", {
                        "message": "Failed to create OpenCode session",
                    }, room=session_id)
                    session_manager.set_status(session_id, "error")
                    return
                
                # Build full prompt with skills context
                full_prompt = f"""你是一个专业的AI图像提示词工程师。

{system_prompt}

用户请求: {content}
目标模型: {model_target}

请根据上述技能和用户请求，生成高质量的提示词。输出JSON格式，包含以下字段:
- positive_prompt: 英文提示词（逗号分隔）
- subject_zh/subject_en: 主体描述（中英双语）
- style: 风格描述
- tech_specs: 技术参数
"""
                
                # Send message and get response
                response = opencode_client.send_message(
                    session_id=opencode_session["id"],
                    content=full_prompt,
                )
                
                if not response:
                    emit("error", {
                        "message": "Failed to get response from OpenCode",
                    }, room=session_id)
                    session_manager.set_status(session_id, "error")
                    return
                
                # Get messages to find the response
                messages = opencode_client.get_messages(opencode_session["id"])
                assistant_messages = [m for m in messages if m.get("role") == "assistant"]
                
                if assistant_messages:
                    raw_response = assistant_messages[-1].get("content", "")
                    
                    # Stream the response in chunks for typing effect
                    chunks = [raw_response[i:i+20] for i in range(0, len(raw_response), 20)]
                    for idx, chunk in enumerate(chunks):
                        emit("stream_delta", {
                            "session_id": session_id,
                            "delta": chunk,
                            "index": idx,
                        }, room=session_id)
                    
                    # Format output
                    formatter = get_output_formatter()
                    formatted = formatter.format_for_model(raw_response, model_target)
                    
                    # Add assistant message to history
                    session_manager.add_message(
                        session_id, 
                        "assistant", 
                        raw_response,
                        metadata=formatted.to_dict(),
                    )
                    
                    # Send complete event with formatted outputs
                    emit("complete", {
                        "session_id": session_id,
                        "prompt_english": formatted.prompt_english,
                        "prompt_json": formatted.prompt_json,
                        "prompt_bilingual": formatted.prompt_bilingual,
                    }, room=session_id)
                
                session_manager.set_status(session_id, "idle")
                emit("status_update", {"status": "idle"}, room=session_id)
                
            except Exception as e:
                emit("error", {
                    "message": f"Error generating prompt: {str(e)}",
                }, room=session_id)
                session_manager.set_status(session_id, "error")
                emit("status_update", {"status": "error"}, room=session_id)
        
        # Submit to thread pool
        _executor.submit(generate_prompt)
    
    @socketio.on("list_skills")
    def handle_list_skills(data: dict[str, Any]) -> None:
        """List all available skills."""
        session_id = data.get("session_id")
        skill_registry = get_skill_registry()
        skills = skill_registry.list_all()
        emit("skills_list", {"skills": skills}, room=session_id)
    
    @socketio.on("abort")
    def handle_abort(data: dict[str, Any]) -> None:
        """Abort current generation."""
        session_id = data.get("session_id")
        if session_id:
            session_manager = get_session_manager()
            session_manager.set_status(session_id, "idle")
            emit("status_update", {"status": "idle"}, room=session_id)
            emit("debug_log", {
                "level": "WARN",
                "module": "SocketHandler",
                "message": "Generation aborted by user",
            }, room=session_id)
