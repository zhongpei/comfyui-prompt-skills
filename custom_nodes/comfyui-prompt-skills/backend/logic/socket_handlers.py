"""
Tier 2: WebSocket Event Handlers

Implements all WebSocket events for real-time communication between
Vue frontend and Opencode Core backend.

Debug Mode: Set COMFYUI_PROMPT_SKILLS_DEBUG=1 to enable detailed logging.
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
    get_debug_emitter,
    debug_log,
    DEBUG_MODE,
)

# Thread pool for async execution
_executor = ThreadPoolExecutor(max_workers=4)


def register_handlers(socketio: SocketIO) -> None:
    """Register all WebSocket event handlers."""
    
    debug_log("SocketHandlers", f"Registering WebSocket handlers (debug_mode={DEBUG_MODE})")
    
    @socketio.on("connect")
    def handle_connect() -> None:
        """Handle new WebSocket connection."""
        session_id = request.args.get("session_id")
        client_sid = request.sid
        
        debug_log("SocketHandler", f"→ connect: session_id={session_id}, client_sid={client_sid}")
        
        if session_id:
            # Join the room for this session
            join_room(session_id)
            
            # Get or create session
            session_manager = get_session_manager()
            session = session_manager.get_or_create_session(session_id)
            
            debug_log("SocketHandler", f"  Session created/retrieved: status={session.status}, skills={session.skills}")
            
            # Send current state
            emit("sync_state", session.to_dict())
            emit("debug_log", {
                "level": "INFO",
                "module": "SocketHandler",
                "message": f"Connected to session: {session_id}",
            })
            
            # Auto-fetch skills list on connect
            skill_registry = get_skill_registry()
            skills = skill_registry.list_all()
            debug_log("SocketHandler", f"  Auto-sending skills list: {len(skills)} skills found")
            emit("skills_list", {"skills": skills})
    
    @socketio.on("disconnect")
    def handle_disconnect() -> None:
        """Handle WebSocket disconnection."""
        session_id = request.args.get("session_id")
        debug_log("SocketHandler", f"← disconnect: session_id={session_id}")
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
        debug_log("SocketHandler", f"→ configure: session_id={session_id}, data={data}")
        
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
            debug_log("SocketHandler", f"  Config updated: skills={session.skills}")
            emit("debug_log", {
                "level": "INFO",
                "module": "SocketHandler",
                "message": f"Configuration updated: skills={session.skills}",
            }, room=session_id)
            emit("sync_state", session.to_dict(), room=session_id)
        else:
            debug_log("SocketHandler", f"  ERROR: Session not found: {session_id}", level="ERROR")
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
        
        debug_log("SocketHandler", f"→ user_message: session_id={session_id}, content={content[:50]}...")
        
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
            debug_log("SocketHandler", f"  ERROR: Session not found: {session_id}", level="ERROR")
            emit("error", {"message": f"Session not found: {session_id}"})
            return
        
        session_manager.set_status(session_id, "working")
        emit("status_update", {"status": "working"}, room=session_id)
        
        # Add user message to history
        session_manager.add_message(session_id, "user", content)
        
        # Create debug emitter for this request
        def emit_to_room(event: str, data: dict, room: str) -> None:
            socketio.emit(event, data, room=room)
        
        debug = get_debug_emitter(emit_to_room, session_id)
        
        # Execute prompt generation in thread pool
        def generate_prompt() -> None:
            try:
                debug.info("PromptGenerator", f"Starting generation for: {content[:50]}...")
                
                # Get skill registry and build system prompt
                skill_registry = get_skill_registry()
                debug.debug("SkillRegistry", f"Loading skills: {session.skills}")
                system_prompt = skill_registry.get_combined_prompt(session.skills)
                
                if system_prompt:
                    debug.info("SkillRegistry", f"Loaded {len(session.skills)} skills, prompt length: {len(system_prompt)}")
                else:
                    debug.warn("SkillRegistry", "No skills loaded or empty system prompt")
                
                # Get OpenCode client
                opencode_client = get_opencode_client()
                debug.debug("OpenCode", "Checking OpenCode server status...")
                
                # Ensure server is running
                if not opencode_client.ensure_server_running():
                    debug.error("OpenCode", "OpenCode Server is not available")
                    socketio.emit("error", {
                        "message": "OpenCode Server is not available. Please ensure 'opencode' is installed.",
                    }, room=session_id)
                    session_manager.set_status(session_id, "error")
                    return
                
                debug.info("OpenCode", "OpenCode Server is running")
                
                # Create or get OpenCode session
                debug.debug("OpenCode", "Creating OpenCode session...")
                opencode_session = opencode_client.create_session(
                    title=f"PromptSkills-{session_id[:8]}"
                )
                
                if not opencode_session:
                    debug.error("OpenCode", "Failed to create OpenCode session")
                    socketio.emit("error", {
                        "message": "Failed to create OpenCode session",
                    }, room=session_id)
                    session_manager.set_status(session_id, "error")
                    return
                
                debug.info("OpenCode", f"OpenCode session created: id={opencode_session.get('id', 'unknown')}")
                
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
                
                debug.debug("OpenCode", f"Sending message to OpenCode (length={len(full_prompt)})")
                
                # Send message and get response
                response = opencode_client.send_message(
                    session_id=opencode_session["id"],
                    content=full_prompt,
                )
                
                if not response:
                    debug.error("OpenCode", "Failed to get response from OpenCode")
                    socketio.emit("error", {
                        "message": "Failed to get response from OpenCode",
                    }, room=session_id)
                    session_manager.set_status(session_id, "error")
                    return
                
                debug.info("OpenCode", "Response received from OpenCode")
                
                # Get messages to find the response
                messages = opencode_client.get_messages(opencode_session["id"])
                debug.debug("OpenCode", f"Retrieved {len(messages)} messages from session")
                debug.debug("OpenCode", f"Raw messages: {messages}") # Added debug log
                
                assistant_messages = [m for m in messages if m.get("role") == "assistant"]
                
                if assistant_messages:
                    raw_response = assistant_messages[-1].get("content", "")
                    debug.info("OpenCode", f"Assistant response: {len(raw_response)} chars")
                    
                    # Stream the response in chunks for typing effect
                    chunks = [raw_response[i:i+20] for i in range(0, len(raw_response), 20)]
                    for idx, chunk in enumerate(chunks):
                        socketio.emit("stream_delta", {
                            "session_id": session_id,
                            "delta": chunk,
                            "index": idx,
                        }, room=session_id)
                    
                    # Format output
                    formatter = get_output_formatter()
                    formatted = formatter.format_for_model(raw_response, model_target)
                    debug.debug("Formatter", f"Formatted output: english={len(formatted.prompt_english)} chars")
                    
                    # Add assistant message to history
                    session_manager.add_message(
                        session_id, 
                        "assistant", 
                        raw_response,
                        metadata=formatted.to_dict(),
                    )
                    
                    # Send complete event with formatted outputs
                    socketio.emit("complete", {
                        "session_id": session_id,
                        "prompt_english": formatted.prompt_english,
                        "prompt_json": formatted.prompt_json,
                        "prompt_bilingual": formatted.prompt_bilingual,
                    }, room=session_id)
                    
                    debug.info("PromptGenerator", "Generation complete!")
                else:
                    debug.warn("OpenCode", "No assistant message found in response")
                    # Log all messages for debugging
                    for i, msg in enumerate(messages):
                        debug.warn("OpenCode", f"  Message[{i}]: role={msg.get('role')}, content={str(msg.get('content'))[:100]}...")

                
                session_manager.set_status(session_id, "idle")
                socketio.emit("status_update", {"status": "idle"}, room=session_id)
                
            except Exception as e:
                debug.error("PromptGenerator", f"Exception: {str(e)}")
                import traceback
                debug.debug("PromptGenerator", f"Traceback: {traceback.format_exc()}")
                socketio.emit("error", {
                    "message": f"Error generating prompt: {str(e)}",
                }, room=session_id)
                session_manager.set_status(session_id, "error")
                socketio.emit("status_update", {"status": "error"}, room=session_id)
        
        # Submit to thread pool
        debug_log("SocketHandler", "  Submitting generation task to thread pool")
        _executor.submit(generate_prompt)
    
    @socketio.on("list_skills")
    def handle_list_skills(data: dict[str, Any]) -> None:
        """List all available skills."""
        session_id = data.get("session_id")
        debug_log("SocketHandler", f"→ list_skills: session_id={session_id}")
        
        skill_registry = get_skill_registry()
        skills = skill_registry.list_all()
        
        debug_log("SocketHandler", f"  Found {len(skills)} skills: {[s['id'] for s in skills]}")
        emit("skills_list", {"skills": skills}, room=session_id)
    
    @socketio.on("abort")
    def handle_abort(data: dict[str, Any]) -> None:
        """Abort current generation."""
        session_id = data.get("session_id")
        debug_log("SocketHandler", f"→ abort: session_id={session_id}")
        
        if session_id:
            session_manager = get_session_manager()
            session_manager.set_status(session_id, "idle")
            emit("status_update", {"status": "idle"}, room=session_id)
            emit("debug_log", {
                "level": "WARN",
                "module": "SocketHandler",
                "message": "Generation aborted by user",
            }, room=session_id)
    
    debug_log("SocketHandlers", "All handlers registered successfully")

