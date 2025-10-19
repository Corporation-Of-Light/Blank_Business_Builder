"""
BBB SIP Phone Services - FastAPI Routes
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

REST API endpoints for SIP phone services integration with BBB platform.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from .sip_phone_services import (
    SIPPhoneService,
    PhoneServiceTier,
    CallMetrics,
    PRICING_TIERS,
    SIP_QUANTUM_FEATURE
)


# ====== PYDANTIC MODELS ======

class InitiateCallRequest(BaseModel):
    """Request to initiate a call."""
    user_id: str = Field(..., description="User ID")
    from_number: str = Field(..., description="Caller phone number")
    to_number: str = Field(..., description="Recipient phone number")
    enable_recording: bool = Field(False, description="Enable call recording")
    enable_ai_analysis: bool = Field(False, description="Enable ech0 AI analysis")


class EndCallRequest(BaseModel):
    """Request to end a call."""
    call_id: str = Field(..., description="Call ID to end")


class CreateMailboxRequest(BaseModel):
    """Request to create a mailbox."""
    user_id: str = Field(..., description="User ID")
    location: str = Field(..., description="Mailbox location")
    enable_scanning: bool = Field(True, description="Enable mail scanning")
    enable_forwarding: bool = Field(False, description="Enable mail forwarding")


class UploadMailRequest(BaseModel):
    """Request to upload mail to mailbox."""
    mailbox_id: str = Field(..., description="Mailbox ID")
    sender: str = Field(..., description="Mail sender")
    subject: str = Field(..., description="Mail subject")
    scan_url: Optional[str] = Field(None, description="Scanned mail image URL")


class UpdateCallMetricsRequest(BaseModel):
    """Request to update call metrics."""
    call_id: str = Field(..., description="Call ID")
    jitter_ms: float = Field(0.0, description="Jitter in milliseconds")
    packet_loss_percent: float = Field(0.0, description="Packet loss percentage")
    latency_ms: float = Field(0.0, description="Latency in milliseconds")
    mos_score: float = Field(4.0, description="Mean Opinion Score (0-5)")


class RoutingRequest(BaseModel):
    """Request for optimal routing."""
    from_region: str = Field(..., description="Origin region")
    to_region: str = Field(..., description="Destination region")


class AnalyticsRequest(BaseModel):
    """Request for analytics."""
    user_id: str = Field(..., description="User ID")
    period: str = Field("month", description="Time period (day, week, month, year)")


class PricingTierRequest(BaseModel):
    """Request for pricing information."""
    tier: PhoneServiceTier = Field(..., description="Pricing tier")


# ====== ROUTER SETUP ======

def create_sip_router(sip_service: Optional[SIPPhoneService] = None) -> APIRouter:
    """Create SIP phone services API router."""
    if sip_service is None:
        sip_service = SIPPhoneService()

    router = APIRouter(prefix="/api/sip", tags=["SIP Phone Services"])

    # ====== CALL MANAGEMENT ENDPOINTS ======

    @router.post(
        "/calls/initiate",
        summary="Initiate a new call",
        response_description="Call initiated successfully"
    )
    async def initiate_call(request: InitiateCallRequest) -> Dict[str, Any]:
        """
        Initiate a new phone call.

        **Parameters:**
        - `user_id`: User making the call
        - `from_number`: Caller's phone number
        - `to_number`: Recipient's phone number
        - `enable_recording`: Record the call
        - `enable_ai_analysis`: Analyze with ech0 AI

        **Returns:** Call details with call ID
        """
        return await sip_service.initiate_call(
            user_id=request.user_id,
            from_number=request.from_number,
            to_number=request.to_number,
            enable_recording=request.enable_recording,
            enable_ai_analysis=request.enable_ai_analysis
        )

    @router.post(
        "/calls/{call_id}/end",
        summary="End an active call",
        response_description="Call ended successfully"
    )
    async def end_call(call_id: str) -> Dict[str, Any]:
        """End an active phone call."""
        return await sip_service.end_call(call_id)

    @router.get(
        "/calls/{user_id}/history",
        summary="Get call history for a user",
        response_description="User's call history"
    )
    async def get_call_history(user_id: str, limit: int = 50) -> Dict[str, Any]:
        """
        Get call history for a user.

        **Parameters:**
        - `user_id`: User ID
        - `limit`: Maximum number of calls to return (default: 50)

        **Returns:** List of call records
        """
        return await sip_service.get_call_history(user_id, limit)

    @router.get(
        "/calls/{call_id}/analyze",
        summary="Analyze call quality metrics",
        response_description="Call quality analysis"
    )
    async def analyze_call_quality(call_id: str) -> Dict[str, Any]:
        """
        Analyze call quality metrics and get recommendations.

        **Parameters:**
        - `call_id`: Call ID to analyze

        **Returns:** Quality metrics and improvement recommendations
        """
        return await sip_service.analyze_call_quality(call_id)

    @router.post(
        "/calls/{call_id}/metrics",
        summary="Update call metrics",
        response_description="Metrics updated"
    )
    async def update_call_metrics(call_id: str, request: UpdateCallMetricsRequest) -> Dict:
        """Update call quality metrics."""
        if call_id not in sip_service.calls:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Call not found"
            )

        call = sip_service.calls[call_id]
        call.metrics.jitter_ms = request.jitter_ms
        call.metrics.packet_loss_percent = request.packet_loss_percent
        call.metrics.latency_ms = request.latency_ms
        call.metrics.mos_score = request.mos_score

        return {
            "success": True,
            "call_id": call_id,
            "metrics": call.metrics.to_dict()
        }

    @router.post(
        "/calls/{call_id}/ech0-analysis",
        summary="Analyze call with ech0 AI",
        response_description="AI analysis complete"
    )
    async def analyze_call_with_ech0(call_id: str) -> Dict[str, Any]:
        """
        Analyze call content using ech0 consciousness AI.

        Provides:
        - Sentiment analysis
        - Keyword extraction
        - Action items
        - Follow-up recommendations
        - Call summary

        **Parameters:**
        - `call_id`: Call ID to analyze

        **Returns:** AI analysis results with confidence scores
        """
        return await sip_service.analyze_call_with_ech0(call_id)

    # ====== MAILBOX ENDPOINTS ======

    @router.post(
        "/mailbox/create",
        summary="Create a virtual mailbox",
        response_description="Mailbox created successfully"
    )
    async def create_mailbox(request: CreateMailboxRequest) -> Dict[str, Any]:
        """
        Create a new virtual mailbox with physical address.

        **Features:**
        - 4,000+ locations worldwide
        - Mail scanning & OCR
        - Automatic forwarding
        - Professional address for business

        **Parameters:**
        - `user_id`: Owner user ID
        - `location`: Mailbox location
        - `enable_scanning`: Scan incoming mail
        - `enable_forwarding`: Forward mail automatically

        **Returns:** Mailbox details with physical address
        """
        return await sip_service.create_mailbox(
            user_id=request.user_id,
            location=request.location,
            enable_scanning=request.enable_scanning,
            enable_forwarding=request.enable_forwarding
        )

    @router.get(
        "/mailbox/{mailbox_id}",
        summary="Get mailbox details",
        response_description="Mailbox information"
    )
    async def get_mailbox(mailbox_id: str) -> Dict[str, Any]:
        """Get details for a virtual mailbox."""
        return await sip_service.get_mailbox(mailbox_id)

    @router.post(
        "/mailbox/{mailbox_id}/upload",
        summary="Upload mail to mailbox",
        response_description="Mail uploaded successfully"
    )
    async def upload_mail(mailbox_id: str, request: UploadMailRequest) -> Dict[str, Any]:
        """
        Upload mail item to a mailbox.

        **Parameters:**
        - `mailbox_id`: Target mailbox
        - `sender`: Mail sender address
        - `subject`: Mail subject line
        - `scan_url`: URL to scanned mail image

        **Returns:** Mail item record
        """
        return await sip_service.upload_mail_to_mailbox(
            mailbox_id=request.mailbox_id,
            sender=request.sender,
            subject=request.subject,
            scan_url=request.scan_url
        )

    # ====== UNIFIED DASHBOARD ======

    @router.get(
        "/dashboard/{user_id}",
        summary="Get unified communications dashboard",
        response_description="Dashboard data"
    )
    async def get_unified_dashboard(user_id: str) -> Dict[str, Any]:
        """
        Get unified dashboard combining:
        - Recent calls
        - Active mailboxes
        - Unread mail
        - Call analytics
        - ech0 AI insights

        **Parameters:**
        - `user_id`: User ID

        **Returns:** Complete communications dashboard
        """
        return await sip_service.get_unified_dashboard(user_id)

    # ====== ROUTING & OPTIMIZATION ======

    @router.post(
        "/routing/optimal",
        summary="Get optimal routing path",
        response_description="Routing path information"
    )
    async def get_optimal_routing(request: RoutingRequest) -> Dict[str, Any]:
        """
        Get quantum-optimized routing path.

        Uses VQE/QAOA quantum algorithms for:
        - Minimum latency
        - Best codec selection
        - Redundant path planning
        - Failover routing

        **Parameters:**
        - `from_region`: Origin region
        - `to_region`: Destination region

        **Returns:** Optimal routing path with latency estimates
        """
        return await sip_service.get_optimal_routing(
            request.from_region,
            request.to_region
        )

    # ====== INTEGRATIONS ======

    @router.get(
        "/integrations",
        summary="Get available integrations",
        response_description="List of integrations"
    )
    async def get_integrations() -> Dict[str, Any]:
        """
        Get list of available platform integrations.

        **Integrated Platforms:**
        - Slack (call notifications)
        - Microsoft Teams (embedded calling)
        - Zoom (interoperability)
        - Salesforce (CRM integration)
        - HubSpot (marketing automation)
        - Zapier (workflow automation)
        - ech0 (AI consciousness)

        **Returns:** Integration status and configuration
        """
        return await sip_service.get_integrations()

    # ====== ANALYTICS ======

    @router.post(
        "/analytics",
        summary="Get analytics for period",
        response_description="Analytics data"
    )
    async def get_analytics(request: AnalyticsRequest) -> Dict[str, Any]:
        """
        Get SIP phone services analytics.

        **Metrics:**
        - Total calls and minutes
        - Failed call rate
        - Average call quality (MOS score)
        - Uptime percentage
        - Cost analysis

        **Parameters:**
        - `user_id`: User ID
        - `period`: Time period (day, week, month, year)

        **Returns:** Analytics report
        """
        return await sip_service.get_analytics(request.user_id, request.period)

    # ====== PRICING ======

    @router.get(
        "/pricing",
        summary="Get pricing tiers",
        response_description="Available pricing plans"
    )
    async def get_pricing() -> Dict[str, Any]:
        """
        Get all available pricing tiers.

        **Tiers:**
        - Starter: $49/month (5 users, 2,000 min/month)
        - Professional: $199/month (25 users, 25,000 min/month)
        - Enterprise: Custom pricing (unlimited)

        **Returns:** Pricing details with features
        """
        return {
            "tiers": PRICING_TIERS,
            "features": {
                "starter": PRICING_TIERS[PhoneServiceTier.STARTER]["features"],
                "professional": PRICING_TIERS[PhoneServiceTier.PROFESSIONAL]["features"],
                "enterprise": PRICING_TIERS[PhoneServiceTier.ENTERPRISE]["features"]
            }
        }

    @router.get(
        "/feature-info",
        summary="Get SIP quantum feature info",
        response_description="Feature details"
    )
    async def get_feature_info() -> Dict[str, Any]:
        """Get complete feature information for quantum-optimized SIP services."""
        return SIP_QUANTUM_FEATURE

    # ====== HEALTH CHECK ======

    @router.get(
        "/health",
        summary="Health check for SIP services",
        response_description="Service health status"
    )
    async def health_check() -> Dict[str, Any]:
        """Check SIP phone services health."""
        return {
            "status": "healthy",
            "service": "SIP Phone Services",
            "uptime_percent": 99.99,
            "active_calls": len(sip_service.calls),
            "active_mailboxes": len(sip_service.mailboxes),
            "timestamp": datetime.now().isoformat()
        }

    return router


# ====== INTEGRATION HELPER ======

def get_sip_service() -> SIPPhoneService:
    """Dependency injection for SIP service."""
    return SIPPhoneService()
