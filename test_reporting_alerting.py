# test_reporting_alerting.py
# Verification Test Harness for Milestone 14: Government Reporting & Alerting Engine.

import requests
import json
import time
import sys

# Prevent Unicode encoding issues in Windows command prompt
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

API_BASE_URL = "http://localhost:8000/api/v1"

def run_reporting_and_alerting_tests():
    print("=========================================")
    print("Government Alerting & Reporting Audits")
    print("=========================================")

    # A. Quick online check
    try:
        health = requests.get("http://localhost:8000/health", timeout=3.0)
        if health.status_code == 200:
            print("[Status OK] Central FastAPI backend is active and reachable.")
        else:
            print(f"[Status Error] Received unexpected status code: {health.status_code}")
            return
    except requests.RequestException:
        print("[Status Error] Central FastAPI backend offline. Please boot backend first.")
        return

    # B. Fetch Latest Violation ID to Test Reporting/Alerting
    print("\nStep 1: Retrieving Active Violations...")
    res_list = requests.get(f"{API_BASE_URL}/violations", timeout=5.0)
    if res_list.status_code != 200 or len(res_list.json()) == 0:
        print("Error: No infractions found in database. Please run test_compliance_engine.py first to seed violations.")
        return
    
    violation = res_list.json()[0]
    violation_id = violation["id"]
    print(f"Targeting active infraction ID: #{violation_id} (Category: {violation['violation_type']}, Severity: {violation['severity_level']})")

    # C. Trigger Real-Time Emergency Alerts (SMS & Email)
    print("\nStep 2: Triggering Real-Time Emergency SMS & SMTP Email Alerts...")
    res_alert = requests.post(f"{API_BASE_URL}/violations/{violation_id}/alert", timeout=5.0)
    if res_alert.status_code == 200:
        a_data = res_alert.json()
        print("Alert Dispatched Successfully:")
        print(f"  - Cellular Gateway  : {a_data['sms']['gateway']} (Status: {a_data['sms']['status']})")
        print(f"  - SMS Dispatch Body : \"{a_data['sms']['body']}\"")
        print(f"  - SMTP Relay Server : {a_data['email']['relay']} (Status: {a_data['email']['status']})")
        print(f"  - Email Relayed To  : {a_data['email']['to']}")
        print("  - Legal Log Saved   : Written to database/alerts.log")
    else:
        print(f"Failed to trigger alerts: {res_alert.text}")

    # D. Trigger Administrative Escalation Hotline Workflow
    print("\nStep 3: Triggering Administrative Escalation Hotlines...")
    # Force mock duration parameter to represent a ticket pending for more than 5 minutes (e.g. 10s)
    res_esc = requests.post(f"{API_BASE_URL}/violations/{violation_id}/escalate?duration_seconds=10", timeout=5.0)
    if res_esc.status_code == 200:
        e_data = res_esc.json()
        if e_data:
            print("Escalation Hotline Dispatched:")
            print(f"  - Escalated To      : {e_data['escalated_to']}")
            print(f"  - Hot Message       : \"{e_data['escalation_message']}\"")
            print(f"  - Escalation Reason : {e_data['reason']}")
        else:
            print("Informational: Infraction severity is low/medium. Escalation skipped.")
    else:
        print(f"Failed to trigger escalation: {res_esc.text}")

    # E. Query Rolling Daily Surveillance Summary Report
    print("\nStep 4: Compiling Rolling Daily Surveillance Summary Report...")
    res_rep = requests.get(f"{API_BASE_URL}/reports/daily/1", timeout=5.0)
    if res_rep.status_code == 200:
        r_data = res_rep.json()
        print("Daily Report compiled successfully:")
        print(f"  - Location ID: {r_data['location_id']}")
        print(f"  - Total Violations (24h) : {r_data['violations_logged']}")
        print(f"  - Total Levied Fines (24h): ₹{r_data['fines_levied_inr']:.2f}")
        print(f"  - Mean Atmospheric AQI   : {r_data['average_aqi']:.2f}")
        print("\nGenerated ASCII Summary Output:")
        print(r_data["ascii_report"])
    else:
        print(f"Failed to query daily report: {res_rep.text}")

    # F. Export Legal E-Challan PDF Layout
    print("\nStep 5: Exporting Official Legal E-Challan Evidence Sheet...")
    res_pdf = requests.get(f"{API_BASE_URL}/violations/{violation_id}/pdf", timeout=5.0)
    if res_pdf.status_code == 200:
        p_data = res_pdf.json()
        print(f"Official Challan generated successfully: {p_data['filename']}")
        print("\nGenerated Legal Evidence PDF ASCII Layout:")
        print(p_data["pdf_ascii_layout"])
    else:
        print(f"Failed to export legal e-challan PDF: {res_pdf.text}")

    print("\n=========================================")
    print("Surveillance Auditing Audits Complete.")
    print("=========================================")

if __name__ == "__main__":
    run_reporting_and_alerting_tests()
