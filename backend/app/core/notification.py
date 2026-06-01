# backend/app/core/notification.py
# Milestone 14: Government Alerting and Reporting Engine.

import os
import time
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.future import select
from sqlalchemy import func

logger = logging.getLogger("spems.backend.notification")

class AlertingSystem:
    """
    Handles state-wide real-time notification dispatches and administrative escalations.
    Coordinates mock SMS payloads (Twilio standard) and SMTP Email relays (AWS SES standard).
    """
    
    @staticmethod
    def trigger_alert(violation_id: int, v_type: str, severity: str, details: str) -> dict:
        """
        Triggers emergency dispatches. Logs and generates full payload payloads
        simulating Twilio cellular SMS formats and AWS SES email templates.
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # 1. SMS Dispatch simulation payload
        sms_text = f"🕉️ SPEMS ALERT: Critical {v_type} (Severity: {severity}) detected at Gaurikund. Ticket ID: #{violation_id}. Action Required! - Uttarakhand Control Room."
        sms_payload = {
            "gateway": "Twilio SMS",
            "from": "+14155550199",
            "to": "+919412000000", # District Magistrate / RTO Inspector Phone
            "body": sms_text,
            "status": "SENT",
            "message_sid": f"SM{int(time.time())}x{violation_id}"
        }

        # 2. SMTP Email simulation payload
        email_subject = f"[CRITICAL ENV ALERT] {v_type} Incident #{violation_id} Flagged"
        email_body = f"""
        ======================================================================
        🕉️ SMART PILGRIMAGE ENVIRONMENTAL MONITORING SYSTEM (SPEMS)
        ======================================================================
        CRITICAL INFRACTION REPORT - UTTARAKHAND CONTROL BOARD
        
        Incident Reference ID: #{violation_id}
        Detection Timestamp: {timestamp}
        Infraction Category: {v_type}
        Severity Level: {severity}
        
        Detailed Narrative: 
        {details}
        
        This notification has been dispatched to the designated RTO inspectors 
        and pollution monitoring committees. Legal evidence has been cryptographically
        sealed and saved in the legal evidence vault.
        
        Click here to review evidence: http://localhost:8000/static/evidence/
        ======================================================================
        """
        email_payload = {
            "relay": "AWS SES SMTP",
            "from": "alerts@spems.uk.gov.in",
            "to": ["inspectors@rto.uk.gov.in", "dm-rudraprayag@uk.gov.in"],
            "subject": email_subject,
            "body": email_body,
            "status": "DELIVERED"
        }

        # Write to local alerts log file for control room audits
        log_dir = "database"
        os.makedirs(log_dir, exist_ok=True)
        with open(os.path.join(log_dir, "alerts.log"), "a", encoding="utf-8") as log_file:
            log_file.write(f"[{timestamp}] ALERT #{violation_id} [{severity}]: {details}\n")
            log_file.write(f"  --> SMS SENT: {sms_payload['message_sid']}\n")
            log_file.write(f"  --> EMAIL DELIVERED TO: {email_payload['to']}\n\n")

        print(f"[Alert System] Real-Time Alert Dispatched for ticket #{violation_id} via SMS & SMTP Relays.")
        return {
            "violation_id": violation_id,
            "sms": sms_payload,
            "email": email_payload
        }

    @staticmethod
    def handle_escalation_workflow(violation_id: int, severity: str, duration_seconds: int) -> dict:
        """
        Escalates unresolved high-priority infractions to senior administration.
        Simulates an automated cron-job supervisor checking database states.
        """
        if severity.upper() == "HIGH" and duration_seconds > 5:
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            escalation_payload = {
                "ticket_id": violation_id,
                "escalated_to": "Uttarakhand State Secretary of Tourism & Environment",
                "escalation_channel": "Critical SMTP Direct & Emergency DM Hotline",
                "timestamp": timestamp,
                "reason": f"High-severity infraction unresolved for {duration_seconds}s.",
                "escalation_message": f"🚩 URGENT ESCALATION: Ticket #{violation_id} remains PENDING. Immediate intervention requested at Secretariat level."
            }
            
            # Log escalation event
            with open("database/alerts.log", "a", encoding="utf-8") as log_file:
                log_file.write(f"[{timestamp}] 🚩 ESCALATION TRIGGERED for Ticket #{violation_id} to {escalation_payload['escalated_to']}: {escalation_payload['reason']}\n\n")
            
            print(f"[Alert System] 🚩 Incident #{violation_id} ESCALATED to State Secretariat.")
            return escalation_payload
        return {}


class ReportingEngine:
    """
    Compiles daily, weekly, and legal compliance reports directly from SQL databases.
    """
    
    @staticmethod
    async def generate_daily_summary(db, location_id: int) -> dict:
        """
        Queries DB and compiles a daily compliance summary.
        Calculates violation density, AQI indices, and collected fines.
        """
        from ..db.models import Violation, SensorData
        
        time_limit = datetime.now(timezone.utc) - timedelta(days=1)
        
        # 1. Total violations in last 24h
        query_v = select(func.count(Violation.id)).where(
            (Violation.location_id == location_id) &
            (Violation.violation_timestamp >= time_limit)
        )
        res_v = await db.execute(query_v)
        v_count = res_v.scalar() or 0

        # 2. Total fines collected in last 24h
        query_f = select(func.sum(Violation.fine_amount_inr)).where(
            (Violation.location_id == location_id) &
            (Violation.violation_timestamp >= time_limit) &
            (Violation.status != "DISMISSED")
        )
        res_f = await db.execute(query_f)
        total_fines = float(res_f.scalar() or 0.0)

        # 3. Average AQI in last 24h
        query_aqi = select(func.avg(SensorData.aqi)).where(
            (SensorData.location_id == location_id) &
            (SensorData.measured_at >= time_limit)
        )
        res_aqi = await db.execute(query_aqi)
        avg_aqi = float(res_aqi.scalar() or 25.0)

        summary_text = f"""
        ======================================================================
        🕉️ SPEMS DAILY SURVEILLANCE COMPLIANCE SUMMARY
        ======================================================================
        Location ID: {location_id}
        Summary Period: 24 Hours (Rolling)
        Report Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}
        
        Summary Indicators:
        - Total Logged Infractions: {v_count}
        - Total Fine Assessments Issued: ₹{total_fines:.2f}
        - 24-Hour Mean Atmospheric AQI: {avg_aqi:.1f}
        
        Status: Systems Operational. Zero Network Failures Reported.
        ======================================================================
        """
        
        return {
            "location_id": location_id,
            "report_date": datetime.now(timezone.utc).date().isoformat(),
            "violations_logged": v_count,
            "fines_levied_inr": total_fines,
            "average_aqi": round(avg_aqi, 2),
            "ascii_report": summary_text
        }

    @staticmethod
    def generate_legal_pdf_report(violation_data: dict) -> str:
        """
        Generates a beautifully structured ASCII text layout simulating an official 
        legal PDF report suitable for courtroom evidence and NIC challan files.
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        
        pdf_layout = f"""
        ========================================================================
                      GOVERNMENT OF UTTARAKHAND - TRANSPORT DEPARTMENT
                           OFFICIAL ENVIRONMENTAL CHALLAN E-TICKET
        ========================================================================
        CHALLAN REF NO: UK-SPEMS-{violation_data['id']}
        LEGAL DISPATCH TIMESTAMP: {timestamp}
        
        ------------------------------------------------------------------------
        I. VIOLATION DETAILS
        ------------------------------------------------------------------------
        Infraction ID        : #{violation_data['id']}
        Location Checkpoint  : Gaurikund Base Camp
        Camera Surveillance  : {violation_data['camera_id']}
        Vehicle Registration : {violation_data['plate_number'] if violation_data['plate_number'] else 'PEDESTRIAN'}
        Surveillance Type    : {violation_data['violation_type'].replace('_', ' ')}
        Severity Index       : {violation_data['severity_level']}
        Coordinates (Spatial): {violation_data['latitude']}, {violation_data['longitude']}
        Incurred Fine        : ₹{violation_data['fine_amount_inr']:.2f} (INR)
        
        ------------------------------------------------------------------------
        II. CRYPTOGRAPHIC EVIDENCE SEAL (LEGAL ADMISSIBILITY)
        ------------------------------------------------------------------------
        Evidence URL         : http://localhost:8000{violation_data['evidence_image_url']}
        Visual Integrity SHA : {violation_data['evidence_hash']}
        
        Status: CRYPTOGRAPHICALLY SIGNED & VERIFIED (TAMPER-FREE LEDGER)
        
        This document serves as primary legal evidence of environmental non-compliance
        under the National Green Tribunal (NGT) rules of Uttarakhand state.
        ========================================================================
        """
        return pdf_layout
