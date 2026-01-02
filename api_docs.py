"""
API Documentation Generator for Mental Health Chatbot
Implements OpenAPI/Swagger specification for all endpoints
"""

from flask import Blueprint, jsonify, render_template_string
from typing import Dict, List

# Create Blueprint for API docs
api_docs_bp = Blueprint('api_docs', __name__)


# ========== OpenAPI Specification ==========

OPENAPI_SPEC = {
    "openapi": "3.0.3",
    "info": {
        "title": "MindSpace Mental Health Chatbot API",
        "description": """
# MindSpace API Documentation

AI-powered mental health chatbot API with dual LLM support, clinical assessments, 
crisis detection, and comprehensive analytics.

## Features
- 💬 **Chat API** - Context-aware AI conversations
- 📊 **Assessments** - PHQ-9 and GAD-7 clinical screenings
- 🔐 **Authentication** - User registration and login
- 📈 **Analytics** - User insights and trends
- 🆘 **Crisis Detection** - Real-time safety monitoring
- 💾 **Caching** - Optimized response times

## Authentication
Most endpoints require session authentication. Login via `/api/auth/login` to obtain a session.

## Rate Limiting
- Standard endpoints: 60 requests/minute
- Chat endpoints: 20 requests/minute
- Assessment endpoints: 10 requests/minute

## Error Handling
All errors return JSON with `error` field and appropriate HTTP status code.
        """,
        "version": "2.0.0",
        "contact": {
            "name": "MindSpace Support",
            "email": "support@mindspace.app"
        },
        "license": {
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT"
        }
    },
    "servers": [
        {
            "url": "http://localhost:5000",
            "description": "Development server"
        }
    ],
    "tags": [
        {"name": "Chat", "description": "AI chatbot conversation endpoints"},
        {"name": "Assessments", "description": "Clinical mental health assessments"},
        {"name": "Authentication", "description": "User authentication and registration"},
        {"name": "Analytics", "description": "User insights and system analytics"},
        {"name": "Memory & Cache", "description": "Conversation memory and caching"},
        {"name": "Health", "description": "System health and monitoring"},
        {"name": "Sentiment", "description": "Sentiment analysis endpoints"}
    ],
    "paths": {
        "/": {
            "get": {
                "tags": ["Pages"],
                "summary": "Home Page",
                "description": "Renders the main chat interface",
                "responses": {
                    "200": {"description": "HTML page rendered successfully"}
                }
            }
        },
        "/assessments": {
            "get": {
                "tags": ["Pages"],
                "summary": "Assessments Page",
                "description": "Renders the clinical assessments interface",
                "responses": {
                    "200": {"description": "HTML page rendered successfully"}
                }
            }
        },
        "/ask": {
            "post": {
                "tags": ["Chat"],
                "summary": "Send Chat Message",
                "description": "Send a message to the AI chatbot and receive a response. Includes crisis detection and context awareness.",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/x-www-form-urlencoded": {
                            "schema": {
                                "type": "object",
                                "required": ["query"],
                                "properties": {
                                    "query": {
                                        "type": "string",
                                        "description": "User message to the chatbot",
                                        "example": "I've been feeling anxious lately"
                                    }
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "response": {"type": "string", "description": "AI response"},
                                        "crisis_detected": {"type": "boolean", "description": "Whether crisis was detected"},
                                        "crisis_level": {"type": "string", "description": "Crisis severity level"},
                                        "crisis_resources": {"type": "object", "description": "Emergency resources"},
                                        "cached": {"type": "boolean", "description": "Whether response was cached"},
                                        "sentiment": {"type": "object", "description": "Sentiment analysis results"}
                                    }
                                },
                                "example": {
                                    "response": "I hear that you've been feeling anxious. That's a common experience...",
                                    "crisis_detected": False,
                                    "cached": False,
                                    "sentiment": {
                                        "sentiment": "negative",
                                        "score": -0.3,
                                        "primary_emotion": "anxiety"
                                    }
                                }
                            }
                        }
                    },
                    "500": {"description": "Internal server error"}
                }
            }
        },
        "/api/assessment/phq9": {
            "get": {
                "tags": ["Assessments"],
                "summary": "Get PHQ-9 Questions",
                "description": "Retrieve PHQ-9 depression screening questions and options",
                "responses": {
                    "200": {
                        "description": "PHQ-9 assessment data",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "title": {"type": "string"},
                                        "description": {"type": "string"},
                                        "questions": {"type": "array", "items": {"type": "string"}},
                                        "options": {"type": "array", "items": {"type": "object"}}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "post": {
                "tags": ["Assessments"],
                "summary": "Submit PHQ-9 Assessment",
                "description": "Submit PHQ-9 answers and receive score interpretation",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["answers"],
                                "properties": {
                                    "answers": {
                                        "type": "array",
                                        "items": {"type": "integer", "minimum": 0, "maximum": 3},
                                        "minItems": 9,
                                        "maxItems": 9,
                                        "description": "Array of 9 answers (0-3 each)",
                                        "example": [1, 2, 1, 0, 2, 1, 1, 0, 1]
                                    }
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Assessment results",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "integer"},
                                        "score": {"type": "integer"},
                                        "max_score": {"type": "integer"},
                                        "interpretation": {"type": "object"},
                                        "crisis_alert": {"type": "object", "nullable": True}
                                    }
                                }
                            }
                        }
                    },
                    "400": {"description": "Invalid answers"}
                }
            }
        },
        "/api/assessment/gad7": {
            "get": {
                "tags": ["Assessments"],
                "summary": "Get GAD-7 Questions",
                "description": "Retrieve GAD-7 anxiety screening questions and options",
                "responses": {
                    "200": {"description": "GAD-7 assessment data"}
                }
            },
            "post": {
                "tags": ["Assessments"],
                "summary": "Submit GAD-7 Assessment",
                "description": "Submit GAD-7 answers and receive score interpretation",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["answers"],
                                "properties": {
                                    "answers": {
                                        "type": "array",
                                        "items": {"type": "integer"},
                                        "minItems": 7,
                                        "maxItems": 7
                                    }
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {"description": "Assessment results"},
                    "400": {"description": "Invalid answers"}
                }
            }
        },
        "/api/assessment/history": {
            "get": {
                "tags": ["Assessments"],
                "summary": "Get Assessment History",
                "description": "Retrieve user's assessment history",
                "responses": {
                    "200": {
                        "description": "Assessment history",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "history": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "id": {"type": "integer"},
                                                    "type": {"type": "string"},
                                                    "score": {"type": "integer"},
                                                    "severity": {"type": "string"},
                                                    "date": {"type": "string"}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/api/auth/register": {
            "post": {
                "tags": ["Authentication"],
                "summary": "Register New User",
                "description": "Create a new user account",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["username", "email", "password"],
                                "properties": {
                                    "username": {"type": "string", "minLength": 3},
                                    "email": {"type": "string", "format": "email"},
                                    "password": {"type": "string", "minLength": 8},
                                    "first_name": {"type": "string"},
                                    "last_name": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {"description": "Registration successful"},
                    "400": {"description": "Invalid input or user exists"}
                }
            }
        },
        "/api/auth/login": {
            "post": {
                "tags": ["Authentication"],
                "summary": "User Login",
                "description": "Authenticate user and create session",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["email", "password"],
                                "properties": {
                                    "email": {"type": "string", "format": "email"},
                                    "password": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {"description": "Login successful"},
                    "401": {"description": "Invalid credentials"}
                }
            }
        },
        "/api/auth/logout": {
            "post": {
                "tags": ["Authentication"],
                "summary": "User Logout",
                "description": "End user session",
                "responses": {
                    "200": {"description": "Logout successful"}
                }
            }
        },
        "/api/auth/profile": {
            "get": {
                "tags": ["Authentication"],
                "summary": "Get User Profile",
                "description": "Get current user's profile information",
                "responses": {
                    "200": {"description": "Profile data"},
                    "401": {"description": "Not authenticated"}
                }
            },
            "put": {
                "tags": ["Authentication"],
                "summary": "Update Profile",
                "description": "Update user profile information",
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "first_name": {"type": "string"},
                                    "last_name": {"type": "string"},
                                    "email": {"type": "string", "format": "email"}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {"description": "Profile updated"},
                    "401": {"description": "Not authenticated"}
                }
            }
        },
        "/api/auth/change-password": {
            "post": {
                "tags": ["Authentication"],
                "summary": "Change Password",
                "description": "Change user's password",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["current_password", "new_password"],
                                "properties": {
                                    "current_password": {"type": "string"},
                                    "new_password": {"type": "string", "minLength": 8}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {"description": "Password changed"},
                    "400": {"description": "Invalid current password"}
                }
            }
        },
        "/api/auth/preferences": {
            "get": {
                "tags": ["Authentication"],
                "summary": "Get Preferences",
                "description": "Get user preferences",
                "responses": {
                    "200": {"description": "User preferences"}
                }
            },
            "put": {
                "tags": ["Authentication"],
                "summary": "Update Preferences",
                "description": "Update user preferences",
                "responses": {
                    "200": {"description": "Preferences updated"}
                }
            }
        },
        "/api/analytics/user-stats": {
            "get": {
                "tags": ["Analytics"],
                "summary": "Get User Statistics",
                "description": "Get comprehensive user statistics",
                "responses": {
                    "200": {
                        "description": "User statistics",
                        "content": {
                            "application/json": {
                                "example": {
                                    "user_id": 1,
                                    "total_conversations": 45,
                                    "total_assessments": 8,
                                    "crisis_events": 2,
                                    "latest_phq9": {"score": 12, "date": "2025-12-31"},
                                    "days_active": 30
                                }
                            }
                        }
                    }
                }
            }
        },
        "/api/analytics/trends/{assessment_type}": {
            "get": {
                "tags": ["Analytics"],
                "summary": "Get Assessment Trends",
                "description": "Get assessment score trends over time",
                "parameters": [
                    {
                        "name": "assessment_type",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string", "enum": ["phq9", "gad7"]}
                    },
                    {
                        "name": "days",
                        "in": "query",
                        "schema": {"type": "integer", "default": 30}
                    }
                ],
                "responses": {
                    "200": {"description": "Trend data"}
                }
            }
        },
        "/api/analytics/crisis-patterns": {
            "get": {
                "tags": ["Analytics"],
                "summary": "Get Crisis Patterns",
                "description": "Analyze crisis event patterns",
                "parameters": [
                    {"name": "days", "in": "query", "schema": {"type": "integer", "default": 30}}
                ],
                "responses": {
                    "200": {"description": "Crisis patterns"}
                }
            }
        },
        "/api/analytics/engagement": {
            "get": {
                "tags": ["Analytics"],
                "summary": "Get Engagement Metrics",
                "description": "Get user engagement metrics",
                "responses": {
                    "200": {"description": "Engagement data"}
                }
            }
        },
        "/api/analytics/trajectory": {
            "get": {
                "tags": ["Analytics"],
                "summary": "Get Mental Health Trajectory",
                "description": "Calculate overall mental health trajectory",
                "responses": {
                    "200": {
                        "description": "Trajectory data",
                        "content": {
                            "application/json": {
                                "example": {
                                    "trajectory_score": 65,
                                    "phq9_trend": "improving",
                                    "gad7_trend": "stable",
                                    "overall_status": "Improving"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/api/analytics/system": {
            "get": {
                "tags": ["Analytics"],
                "summary": "Get System Analytics",
                "description": "Get system-wide analytics (admin)",
                "responses": {
                    "200": {"description": "System analytics"}
                }
            }
        },
        "/api/analytics/sentiment-trends": {
            "get": {
                "tags": ["Sentiment"],
                "summary": "Get Sentiment Trends",
                "description": "Get sentiment analysis trends over time",
                "parameters": [
                    {"name": "days", "in": "query", "schema": {"type": "integer", "default": 30}}
                ],
                "responses": {
                    "200": {"description": "Sentiment trends"}
                }
            }
        },
        "/api/memory/clear": {
            "post": {
                "tags": ["Memory & Cache"],
                "summary": "Clear Conversation Memory",
                "description": "Clear conversation memory for current user",
                "responses": {
                    "200": {"description": "Memory cleared"}
                }
            }
        },
        "/api/memory/stats": {
            "get": {
                "tags": ["Memory & Cache"],
                "summary": "Get Memory Stats",
                "description": "Get conversation memory statistics",
                "responses": {
                    "200": {"description": "Memory statistics"}
                }
            }
        },
        "/api/cache/stats": {
            "get": {
                "tags": ["Memory & Cache"],
                "summary": "Get Cache Stats",
                "description": "Get response cache statistics",
                "responses": {
                    "200": {
                        "description": "Cache statistics",
                        "content": {
                            "application/json": {
                                "example": {
                                    "hit_rate": "75.50%",
                                    "hits": 151,
                                    "misses": 49,
                                    "size": 42
                                }
                            }
                        }
                    }
                }
            }
        },
        "/api/cache/clear": {
            "post": {
                "tags": ["Memory & Cache"],
                "summary": "Clear Cache",
                "description": "Clear all cached responses (admin)",
                "responses": {
                    "200": {"description": "Cache cleared"}
                }
            }
        },
        "/api/health": {
            "get": {
                "tags": ["Health"],
                "summary": "Health Check",
                "description": "Get system health status",
                "responses": {
                    "200": {
                        "description": "Health status",
                        "content": {
                            "application/json": {
                                "example": {
                                    "status": "Healthy",
                                    "uptime_seconds": 3600,
                                    "database": "connected",
                                    "llm_primary": "available",
                                    "llm_secondary": "available"
                                }
                            }
                        }
                    }
                }
            }
        }
    },
    "components": {
        "schemas": {
            "Error": {
                "type": "object",
                "properties": {
                    "error": {"type": "string"},
                    "message": {"type": "string"}
                }
            },
            "User": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "username": {"type": "string"},
                    "email": {"type": "string"},
                    "first_name": {"type": "string"},
                    "last_name": {"type": "string"},
                    "is_verified": {"type": "boolean"},
                    "created_at": {"type": "string", "format": "date-time"}
                }
            },
            "AssessmentResult": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "score": {"type": "integer"},
                    "max_score": {"type": "integer"},
                    "severity": {"type": "string"},
                    "interpretation": {"type": "string"},
                    "recommendations": {"type": "array", "items": {"type": "string"}}
                }
            },
            "SentimentAnalysis": {
                "type": "object",
                "properties": {
                    "sentiment": {"type": "string", "enum": ["positive", "negative", "neutral"]},
                    "score": {"type": "number", "minimum": -1, "maximum": 1},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "primary_emotion": {"type": "string"},
                    "risk_level": {"type": "string", "enum": ["low", "moderate", "high", "critical"]}
                }
            }
        },
        "securitySchemes": {
            "sessionAuth": {
                "type": "apiKey",
                "in": "cookie",
                "name": "session"
            }
        }
    }
}


# ========== Swagger UI HTML ==========

SWAGGER_UI_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>MindSpace API Documentation</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
    <style>
        body { margin: 0; padding: 0; }
        .swagger-ui .topbar { display: none; }
        .swagger-ui .info .title { color: #9b87f5; }
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script>
        window.onload = function() {
            SwaggerUIBundle({
                url: "/api/docs/openapi.json",
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIBundle.SwaggerUIStandalonePreset
                ],
                layout: "BaseLayout"
            });
        };
    </script>
</body>
</html>
"""


# ========== Routes ==========

@api_docs_bp.route('/')
def swagger_ui():
    """Render Swagger UI"""
    return render_template_string(SWAGGER_UI_HTML)


@api_docs_bp.route('/openapi.json')
def openapi_spec():
    """Return OpenAPI specification"""
    return jsonify(OPENAPI_SPEC)


@api_docs_bp.route('/endpoints')
def list_endpoints():
    """List all API endpoints"""
    endpoints = []
    for path, methods in OPENAPI_SPEC['paths'].items():
        for method, details in methods.items():
            if method != 'parameters':
                endpoints.append({
                    'method': method.upper(),
                    'path': path,
                    'summary': details.get('summary', ''),
                    'tags': details.get('tags', [])
                })
    
    return jsonify({
        'total_endpoints': len(endpoints),
        'endpoints': endpoints
    })


def get_api_documentation():
    """Return API documentation dict"""
    return OPENAPI_SPEC
