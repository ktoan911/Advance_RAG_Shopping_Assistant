from __future__ import annotations

import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify, request
from flask_cors import CORS

from src.common.logger import get_logger
from src.controller.agent import Agent
from src.infrastructure.controller_service import controller_service

app = Flask(__name__)
CORS(app)
controller = None
is_ready = False
logger = get_logger("ChatbotRAGAPI")
agent = None


def initialize_controller():
    global controller, is_ready, agent

    logger.info("🔄 Đang khởi tạo Chatbot RAG system...")
    start_time = time.time()

    try:
        logger.info("📦 Đang khởi tạo agent")
        agent = Agent()
        logger.info("📚 Đang khởi tạo Message Controller...")
        controller = controller_service.get_controller()

        logger.info("Đang warmup system với test query...")
        _ = controller.get_general_message(
            "Xin chào, bạn có thể giới thiệu về sản phẩm không?"
        )
        controller.delete_history()

        initialization_time = time.time() - start_time
        logger.info(
            f"Hệ thống đã sẵn sàng! Thời gian khởi tạo: {initialization_time:.2f}s"
        )
        logger.info("Server đã sẵn sàng nhận requests...")

        is_ready = True

    except Exception as e:
        logger.error(f"Lỗi khi khởi tạo system: {str(e)}")
        raise e


# Initialize controller on startup
initialize_controller()


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy" if is_ready else "initializing"})


@app.route("/get_message", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        if not data or "input" not in data:
            return jsonify({"error": "Prompt is required"}), 400

        prompt = data["input"]

        # Use existing event loop instead of creating new one
        try:
            start = time.time()

            result = agent.execute(prompt)
            full_query = result.text if hasattr(result, "text") else str(result)
            response_text = controller.get_llm_response(prompt, full_query)

            return jsonify(
                {
                    "response": response_text,
                    "time": time.time() - start,
                    "status": "success",
                }
            )
        except Exception as e:
            logger.info(f"Lỗi khi xử lý MCP agent: {e}")
            return jsonify({"error": str(e), "status": "error"}), 500

    except Exception as e:
        logger.info(f"Lỗi trong endpoint /get_message: {e}")
        return jsonify({"error": str(e), "status": "error"}), 500


@app.route("/get_history", methods=["GET"])
def get_history():
    try:
        return jsonify(
            {
                "history": controller.get_history(),
                "count": len(controller.get_history()),
                "status": "success",
            }
        )
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500


@app.route("/delete_history", methods=["DELETE"])
def delete_history():
    try:
        message = controller.delete_history()
        return jsonify({"message": message, "status": "success"})
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500


@app.route("/config", methods=["GET"])
def get_config():
    """Get current configuration"""
    return jsonify({"num_history": controller.num_history, "status": "success"})


@app.route("/config", methods=["POST"])
def update_config():
    """Update configuration"""
    try:
        data = request.get_json()
        if "num_history" in data:
            controller.num_history = int(data["num_history"])

        return jsonify(
            {
                "message": "Configuration updated successfully",
                "num_history": controller.num_history,
                "status": "success",
            }
        )
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500


@app.route("/export_history", methods=["GET"])
def export_history():
    """Export chat history"""
    try:
        history = controller.get_history()
        return jsonify(
            {
                "history": history,
                "exported_at": time.time(),
                "count": len(history),
                "status": "success",
            }
        )
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found", "status": "error"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error", "status": "error"}), 500


if __name__ == "__main__":
    logger.info("🚀 Starting Flask API server...")
    app.run(host="0.0.0.0", port=5000, debug=True)
