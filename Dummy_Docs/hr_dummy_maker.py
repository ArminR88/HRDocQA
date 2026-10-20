from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
import csv
import json
import os

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "HR_dummy_docs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

styles = getSampleStyleSheet()
title_style = ParagraphStyle("Title", parent=styles["Heading1"], fontSize=18, spaceAfter=20)
body_style = styles["BodyText"]

# ---------------------------------------------------------------------------
# Section content. Each section is (heading, [paragraphs]).
# Extended documents get 10+ sections. Unchanged documents get 5-6.
# Paragraphs are 80-150 chars of real policy text.
# ---------------------------------------------------------------------------

EXTENDED = {
    "employee_handbook": [
        ("Employee Handbook", [
            "Welcome to Acme Corp. This handbook outlines the policies, procedures, and expectations for all employees.",
            "It applies to every employee regardless of contract type, location, or seniority, and it is reviewed annually.",
            "Where a collective agreement applies, that agreement takes precedence over this handbook.",
        ]),
        ("Working Hours", [
            "Standard working hours are 9:00 AM to 5:00 PM, Monday through Friday, with a one-hour unpaid lunch break.",
            "Flexible start times between 8:00 and 10:00 are permitted with manager approval and consistent daily coverage.",
            "Overtime must be approved in advance; unapproved overtime is not compensated.",
        ]),
        ("Code of Conduct", [
            "Employees are expected to act professionally, treat colleagues with respect, and avoid conflicts of interest.",
            "Conflicts of interest must be disclosed to HR in writing within 5 business days of becoming aware of them.",
            "Violations of the code of conduct may result in disciplinary action up to and including termination.",
        ]),
        ("Dress Code", [
            "Business casual attire is expected in the office. Casual dress is permitted on Fridays.",
            "Client-facing meetings require business formal attire regardless of the day of the week.",
            "Safety-sensitive roles must wear the protective equipment specified by Facilities.",
        ]),
        ("Remote Work", [
            "Employees may work remotely up to two days per week with manager approval.",
            "Remote work days must be recorded in the HR portal at least one week in advance.",
            "Employees must remain reachable during core hours (10:00 to 16:00) while working remotely.",
        ]),
        ("Communication Standards", [
            "Email is the official channel for written decisions; chat is for time-sensitive coordination only.",
            "Responses to external correspondence are expected within 2 business days.",
            "Confidential information must not be shared over unapproved messaging applications.",
        ]),
        ("Equipment and Access", [
            "Company equipment is issued on the first day and remains company property at all times.",
            "Lost or damaged equipment must be reported to IT within 24 hours of discovery.",
            "Access badges must not be shared; tailgating into secure areas is prohibited.",
        ]),
        ("Performance Expectations", [
            "Every employee has written goals reviewed at least twice per year in June and December.",
            "Sustained performance below expectations triggers a documented improvement plan.",
            "Promotions require sustained ratings of 'Exceeds Expectations' for at least two consecutive cycles.",
        ]),
        ("Learning and Development", [
            "Each employee receives an annual learning budget of 1,500 EUR for professional development.",
            "Mandatory compliance and security training must be completed by 31 January each year.",
            "Tuition reimbursement up to 5,000 EUR per year is available for job-related degree programs.",
        ]),
        ("Separation and Offboarding", [
            "Employees resigning voluntarily should give at least 2 weeks' written notice to their manager.",
            "Exit interviews are conducted by HR during the final week of employment.",
            "All company equipment must be returned on the last day of employment.",
        ]),
        ("Policy Review", [
            "This handbook is reviewed annually by HR and Legal and reissued each January.",
            "Employees are notified of material changes by email and must acknowledge receipt within 10 days.",
            "Questions about interpretation should be directed to HR, not to individual managers.",
        ]),
    ],
    "leave_policy": [
        ("Urlaubsrichtlinie / Vacation Policy", [
            "Statutory Minimum: Employees are entitled to a minimum of 24 working days of paid vacation per year based on a 6-day work week.",
            "For employees on a 5-day work week, the equivalent entitlement is 20 working days of paid vacation per year.",
            "Additional contractual vacation above the statutory minimum is granted per the employment contract.",
        ]),
        ("Waiting Period", [
            "Full vacation entitlement is acquired after 6 months of employment.",
            "Pro-rata entitlement applies before the 6-month waiting period has elapsed.",
            "Pro-rata calculation is based on completed months of service in the calendar year.",
        ]),
        ("Carryover", [
            "Vacation must be taken in the current calendar year whenever operationally possible.",
            "Carryover to the next year is permitted only for compelling operational or personal reasons.",
            "Carried-over vacation expires on March 31 of the following year and is forfeited thereafter.",
        ]),
        ("Illness During Vacation", [
            "If an employee falls ill during vacation and provides a medical certificate, the days of illness are not counted as vacation.",
            "The medical certificate must be submitted to HR within 3 calendar days of the start of illness.",
            "Illness during vacation does not extend the calendar year for carryover purposes.",
        ]),
        ("Vacation Request", [
            "Vacation requests must be submitted to the manager at least 2 weeks in advance.",
            "Requests spanning more than 10 consecutive working days require HR review in addition to manager approval.",
            "Approved vacation may be revoked only for documented business necessity with written notice.",
        ]),
        ("Special Leave", [
            "Employees are entitled to paid special leave for weddings (1 day) and childbirth of spouse (1 day).",
            "Death of immediate family entitles the employee to 2 days of paid special leave.",
            "Special leave must be requested in writing and approved by the manager before the absence.",
        ]),
        ("Parental Leave Interaction", [
            "Vacation entitlement continues to accrue during statutory parental leave.",
            "Vacation may not be taken concurrently with parental leave benefit periods.",
            "Returning employees may request vacation in the first month after return with shortened notice.",
        ]),
        ("Sick Leave Interaction", [
            "Sick days are not deducted from annual vacation entitlement.",
            "A doctor's certificate is required for sick leave exceeding 3 calendar days.",
            "Repeated short absences may trigger a return-to-work conversation with the manager.",
        ]),
        ("Unpaid Leave", [
            "Unpaid leave may be granted for compelling personal reasons with HR approval.",
            "Unpaid leave exceeding 30 calendar days requires a written agreement signed by both parties.",
            "Social security contributions during unpaid leave are governed by statutory rules.",
        ]),
        ("Recordkeeping", [
            "All vacation taken is recorded in the HR portal within 5 business days of return.",
            "Discrepancies between recorded and actual vacation must be reported to HR immediately.",
            "Vacation records are retained for the duration of employment plus 3 years.",
        ]),
        ("Termination and Payout", [
            "Unused statutory vacation is paid out upon termination where statutory law requires it.",
            "Contractual vacation above the statutory minimum is forfeited on termination unless the contract states otherwise.",
            "Payout is calculated at the employee's base salary on the last day of employment.",
        ]),
    ],
    "sick_leave": [
        ("Krankmeldung / Sick Leave Policy", [
            "Notification: Employees must notify their manager on the first day of illness before the start of their shift.",
            "Notification may be by phone, email, or HR portal; silence is treated as an unexcused absence.",
            "The manager must acknowledge receipt and inform HR on the same day.",
        ]),
        ("Medical Certificate", [
            "A doctor's certificate must be submitted by the third calendar day of illness.",
            "For absences exceeding 5 calendar days, the certificate must state the expected duration.",
            "Certificates are retained by HR for the duration required by statutory recordkeeping rules.",
        ]),
        ("Continued Pay", [
            "The employer continues to pay full salary for up to 6 weeks (42 calendar days) for the same illness.",
            "Continued pay applies only after 4 weeks of employment with the company.",
            "Continued pay is calculated on the regular base salary, excluding overtime and bonuses.",
        ]),
        ("Same Illness Rule", [
            "If an employee is ill with the same condition again within 6 months, the 6-week period is combined.",
            "Combining periods means the employer's obligation may end earlier than the first 6-week period.",
            "The employer must document the combined calculation and inform the employee in writing.",
        ]),
        ("Sick Leave and Vacation", [
            "Sick days are not deducted from annual vacation entitlement.",
            "Illness during approved vacation does not consume vacation days if a certificate is provided.",
            "Vacation days displaced by illness must be re-scheduled within the current calendar year.",
        ]),
        ("Return to Work", [
            "A return-to-work conversation is held with the manager after absences longer than 6 weeks.",
            "The conversation covers fitness for duty, any required accommodations, and a reintegration plan.",
            "A written summary of the conversation is filed with HR and shared with the employee.",
        ]),
        ("Repeated Absences", [
            "Repeated short absences may trigger a formal absence review with HR.",
            "The review considers pattern, duration, and any documented medical cause.",
            "Outcomes range from no action to a documented improvement plan, depending on findings.",
        ]),
        ("Occupational Accidents", [
            "Occupational accidents must be reported to the manager and to Facilities on the same day.",
            "The employer notifies the statutory accident insurance within 3 days of the report.",
            "Return-to-work after an occupational accident follows the same process as general sick leave.",
        ]),
        ("Documentation", [
            "All sick leave is recorded in the HR portal by the manager within 1 business day of notification.",
            "Medical certificates are stored separately from personnel files with restricted access.",
            "Employees may request a copy of their sick leave record at any time.",
        ]),
        ("Escalation", [
            "Disputes about sick leave classification are escalated to the HR Director within 10 business days.",
            "The HR Director's decision is documented and communicated in writing to both parties.",
            "Further appeals follow the standard grievance procedure.",
        ]),
    ],
}

# The remaining extended and unchanged files are built from templates below.
TEMPLATE_SECTIONS = [
    ("Scope and Application", [
        "This policy applies to all employees of Acme Corp regardless of location or contract type.",
        "Contractors and temporary staff are covered where their engagement terms explicitly state so.",
        "Where local law requires a stricter standard, local law takes precedence.",
    ]),
    ("Definitions", [
        "Key terms used in this policy are defined in the glossary maintained by HR.",
        "Definitions are reviewed annually to remain consistent with statutory terminology.",
        "Ambiguities are resolved by HR in consultation with Legal.",
    ]),
    ("Roles and Responsibilities", [
        "Managers are responsible for applying this policy consistently within their teams.",
        "HR is responsible for interpretation, recordkeeping, and periodic review.",
        "Employees are responsible for reading and complying with the policy in force.",
    ]),
    ("Process and Workflow", [
        "Requests and approvals follow the workflow published in the HR portal.",
        "Each step has a named owner and a documented turnaround time.",
        "Exceptions require written approval from the next level of management.",
    ]),
    ("Timelines", [
        "Standard turnaround for a request is 10 business days from submission.",
        "Complex cases may be extended once by 10 business days with written notice.",
        "Urgent cases are escalated to the HR Director on the same business day.",
    ]),
    ("Documentation Requirements", [
        "Supporting documents must be uploaded to the HR portal in PDF or image format.",
        "Originals may be requested by HR for verification at any time.",
        "Documents are retained for the period required by statutory recordkeeping rules.",
    ]),
    ("Approval Authority", [
        "First-line approval rests with the direct manager.",
        "Second-line approval rests with the department head for matters above 2,000 EUR.",
        "Final approval rests with the HR Director for exceptions to this policy.",
    ]),
    ("Exceptions", [
        "Exceptions are granted only in writing and only for documented business or personal reasons.",
        "All exceptions are logged and reviewed quarterly by HR.",
        "Repeated exceptions for the same reason are treated as a signal to revise the policy.",
    ]),
    ("Escalation", [
        "Unresolved disputes are escalated to the HR Director within 10 business days.",
        "The HR Director's decision is documented and communicated in writing.",
        "Further appeals follow the standard grievance procedure.",
    ]),
    ("Recordkeeping and Audit", [
        "All records are stored in the HR system with access controls and audit logs.",
        "Internal audit reviews a sample of records each quarter.",
        "Findings are reported to the HR Director and, where material, to the executive team.",
    ]),
    ("Review Cycle", [
        "This policy is reviewed annually by HR in consultation with Legal.",
        "Material changes are communicated to employees with 30 days' notice.",
        "Employees must acknowledge the current version in the HR portal each year.",
    ]),
]

UNCHANGED_FILES = {
    "onboarding_checklist": [
        ("New Employee Onboarding Checklist", [
            "Day 1: Complete HR paperwork, receive equipment, and attend orientation.",
            "Week 1: Meet your team, complete mandatory compliance training, and set up accounts.",
            "Week 2-4: Shadow a senior colleague and complete role-specific training.",
            "Day 30: Check-in meeting with your manager to review progress.",
            "Day 90: Formal probation review and goal-setting session.",
        ]),
    ],
    "disciplinary_procedure": [
        ("Disciplinary Procedure", [
            "Purpose: This procedure ensures fair and consistent handling of performance or conduct issues.",
            "Verbal Warning: First-level issues are addressed through a documented verbal warning.",
            "Written Warning: Repeated or more serious issues result in a formal written warning.",
            "Final Warning: Serious misconduct may result in a final written warning.",
            "Termination: Gross misconduct or repeated violations may result in termination of employment.",
        ]),
    ],
    "grievance_policy": [
        ("Grievance Policy", [
            "Right to Raise: All employees have the right to raise grievances without fear of retaliation.",
            "Informal Resolution: Employees are encouraged to first raise concerns directly with their manager.",
            "Formal Grievance: Formal grievances must be submitted in writing to HR within 30 days of the incident.",
            "Investigation: HR will investigate and respond within 10 business days.",
            "Appeal: Employees may appeal the outcome to the HR Director within 5 business days.",
        ]),
    ],
    "diversity_inclusion": [
        ("Diversity and Inclusion Policy", [
            "Commitment: Acme Corp is committed to building a diverse and inclusive workforce.",
            "Recruitment: Hiring practices are designed to reduce unconscious bias.",
            "Employee Resource Groups: ERGs for women, LGBTQ+, veterans, and underrepresented groups are supported.",
            "Training: All managers complete annual diversity and inclusion training.",
            "Reporting: Discrimination or bias incidents should be reported to HR immediately.",
        ]),
    ],
    "overtime_policy": [
        ("Overtime Policy", [
            "Eligibility: Non-exempt employees are eligible for overtime pay at 1.5x their regular rate.",
            "Approval: All overtime must be approved in advance by a manager.",
            "Tracking: Employees must record all hours worked accurately in the time-tracking system.",
            "Maximum Hours: Employees should not exceed 60 hours of work per week without HR approval.",
            "Compensatory Time: Exempt employees may receive comp time for weekend work at manager discretion.",
        ]),
    ],
    "referral_program": [
        ("Employee Referral Program", [
            "Eligibility: All employees except HR staff and hiring managers may participate.",
            "Bonus: A 2,000 EUR bonus is paid after the referred employee completes 90 days of employment.",
            "Exclusions: Referrals of former employees who left within the past 12 months are not eligible.",
            "Submission: Referrals must be submitted through the company careers portal.",
            "Payment: Bonuses are paid in the payroll cycle following the 90-day mark.",
        ]),
    ],
    "flexible_working": [
        ("Flexible Working Policy", [
            "Eligibility: All employees who have completed 6 months of service may request flexible working.",
            "Types: Options include remote work, compressed hours, flexitime, and part-time arrangements.",
            "Request Process: Requests must be submitted in writing to your manager 30 days in advance.",
            "Trial Period: Approved arrangements are trialed for 3 months before becoming permanent.",
            "Review: Flexible arrangements are reviewed annually as part of performance discussions.",
        ]),
    ],
    "drug_alcohol": [
        ("Drug and Alcohol Policy", [
            "Zero Tolerance: Acme Corp prohibits the use, possession, or distribution of illegal drugs on company premises.",
            "Alcohol: Alcohol may only be consumed at company-sponsored events with manager approval.",
            "Fitness for Duty: Employees must report to work free from the influence of drugs or alcohol.",
            "Testing: Drug and alcohol testing may be required for safety-sensitive roles.",
            "Support: Employees struggling with substance abuse are encouraged to contact the EAP.",
        ]),
    ],
    "data_privacy": [
        ("Data Privacy and Protection Policy", [
            "Scope: This policy covers all personal and business data collected, stored, or processed by Acme Corp.",
            "GDPR Compliance: Acme Corp complies with GDPR and other applicable data protection laws.",
            "Data Access: Employees may only access data necessary for their role.",
            "Data Breach: Suspected data breaches must be reported to the Data Protection Officer within 24 hours.",
            "Retention: Personal data is retained only as long as necessary for business or legal purposes.",
        ]),
    ],
    "exit_interview": [
        ("Exit Interview Guidelines", [
            "Purpose: Exit interviews gather feedback to improve employee experience and retention.",
            "Timing: Exit interviews are scheduled during the final week of employment.",
            "Format: Interviews may be conducted in person or via video call, lasting 30-45 minutes.",
            "Confidentiality: Feedback is aggregated and anonymized before being shared with leadership.",
            "Optional: Employees may decline an exit interview without any impact on their final pay.",
        ]),
    ],
    "whistleblower_policy": [
        ("Whistleblower Policy", [
            "Protection: Acme Corp prohibits retaliation against employees who report concerns in good faith.",
            "Scope: Reports may cover financial fraud, safety violations, harassment, or other misconduct.",
            "Reporting Channels: Concerns may be reported to HR, Legal, or the anonymous ethics hotline.",
            "Investigation: All reports are investigated promptly and confidentially.",
            "Confidentiality: The identity of the reporter is protected to the extent permitted by law.",
        ]),
    ],
}

# Extended files that are not written by hand above use the template.
EXTENDED_FILES_FROM_TEMPLATE = [
    "parental_leave",
    "maternity_protection",
    "employee_data_change",
    "performance_review",
    "training_development",
    "benefits_guide",
    "workplace_conduct",
    "recruitment_policy",
    "compensation_policy",
    "expense_reimbursement",
    "travel_policy",
    "it_security",
    "termination_offboarding",
    "health_safety",
    "relocation_policy",
]


def build_documents():
    documents = {}
    # Hand-written extended files.
    for name, entries in EXTENDED.items():
        documents[name] = entries
    # Template-driven extended files.
    for name in EXTENDED_FILES_FROM_TEMPLATE:
        title = name.replace("_", " ").title()
        entries = [(title + " Policy", [
            "This section introduces the " + title + " policy and its purpose within Acme Corp.",
            "It states the principles the policy protects and the outcomes it is designed to achieve.",
            "It confirms the policy's scope and its relationship to other company policies.",
        ])]
        entries.extend(TEMPLATE_SECTIONS)
        documents[name] = entries
    # Unchanged files.
    for name, entries in UNCHANGED_FILES.items():
        documents[name] = entries
    return documents


documents = build_documents()

# Keep the Q&A list identical to the original generator.
qa_pairs = [
    {"question": "How many working days of vacation are employees entitled to?", "answer": "24 working days based on a 6-day week, or 20 days for a 5-day week.", "source": "leave_policy.pdf"},
    {"question": "When does vacation carryover to the next year expire?", "answer": "March 31 of the following year.", "source": "leave_policy.pdf"},
    {"question": "Are sick days deducted from vacation?", "answer": "No, sick days are not deducted from annual vacation entitlement.", "source": "leave_policy.pdf"},
    {"question": "How long does the employer continue to pay salary during illness?", "answer": "Up to 6 weeks for the same illness.", "source": "sick_leave.pdf"},
    {"question": "By when must a doctor's certificate be submitted?", "answer": "By the third calendar day of illness.", "source": "sick_leave.pdf"},
    {"question": "Until what age can employees take parental leave?", "answer": "Until the child's third birthday.", "source": "parental_leave.pdf"},
    {"question": "How many hours per week can parents work during parental leave?", "answer": "Up to 30 hours per week.", "source": "parental_leave.pdf"},
    {"question": "How many weeks before parental leave must it be requested?", "answer": "At least 7 weeks before the start date.", "source": "parental_leave.pdf"},
    {"question": "How many weeks before and after childbirth is maternity leave?", "answer": "6 weeks before and 8 weeks after, 12 weeks for premature or multiple births.", "source": "maternity_protection.pdf"},
    {"question": "How quickly must an employee report an address change to HR?", "answer": "Within 2 weeks of moving.", "source": "employee_data_change.pdf"},
    {"question": "How far in advance must a bank account change be submitted for payroll?", "answer": "At least 10 days before the next payroll run.", "source": "employee_data_change.pdf"},
    {"question": "When does a tax class change take effect?", "answer": "From the month of submission.", "source": "employee_data_change.pdf"},
    {"question": "How often are performance reviews conducted?", "answer": "Twice per year, in June and December.", "source": "performance_review.pdf"},
    {"question": "What is the annual learning budget per employee?", "answer": "1,500 EUR per year for professional development.", "source": "training_development.pdf"},
    {"question": "How many days a week can employees work remotely?", "answer": "Up to two days per week with manager approval.", "source": "employee_handbook.pdf"},
    {"question": "What is the daily meal allowance for international travel?", "answer": "100 EUR per day for international travel.", "source": "expense_reimbursement.pdf"},
    {"question": "How long must passwords be and how often rotated?", "answer": "At least 12 characters, rotated every 90 days.", "source": "it_security.pdf"},
    {"question": "How many days of written notice are required for resignation?", "answer": "At least 2 weeks' written notice.", "source": "termination_offboarding.pdf"},
    {"question": "What is the maximum hotel rate for business travel in major cities?", "answer": "250 EUR per night in major cities.", "source": "travel_policy.pdf"},
    {"question": "When must a suspected data breach be reported?", "answer": "Within 24 hours to the Data Protection Officer.", "source": "data_privacy.pdf"},
    {"question": "What is the relocation lump sum amount?", "answer": "Up to 10,000 EUR to cover moving costs.", "source": "relocation_policy.pdf"},
    {"question": "What is the employee referral bonus?", "answer": "2,000 EUR after the referred employee completes 90 days.", "source": "referral_program.pdf"},
    {"question": "How much is the annual wellness stipend?", "answer": "500 EUR per year.", "source": "benefits_guide.pdf"},
]

for name, entries in documents.items():
    filename = name + ".pdf"
    base = name
    filepath = os.path.join(OUTPUT_DIR, filename)

    doc = SimpleDocTemplate(filepath, pagesize=letter)
    story = []
    for index, (title, paragraphs) in enumerate(entries):
        if index > 0:
            story.append(Spacer(1, 24))
        story.append(Paragraph(title, title_style))
        for p in paragraphs:
            story.append(Paragraph(p, body_style))
            story.append(Spacer(1, 12))
    doc.build(story)
    print(f"Created {filepath}")

    lines = []
    for title, paragraphs in entries:
        lines.append(title)
        lines.extend(paragraphs)
        lines.append("")

    txt_path = os.path.join(OUTPUT_DIR, base + ".txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    md = ""
    for title, paragraphs in entries:
        md += f"# {title}\n\n"
        for p in paragraphs:
            md += f"{p}\n\n"
    md_path = os.path.join(OUTPUT_DIR, base + ".md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)

    html_body = ""
    for title, paragraphs in entries:
        html_body += f"<h1>{title}</h1>\n"
        for p in paragraphs:
            html_body += f"<p>{p}</p>\n"
    html = f"<!DOCTYPE html>\n<html><head><meta charset='utf-8'><title>{base}</title></head><body>\n{html_body}</body></html>\n"
    html_path = os.path.join(OUTPUT_DIR, base + ".html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    csv_path = os.path.join(OUTPUT_DIR, base + ".csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["section", "paragraph"])
        for title, paragraphs in entries:
            for p in paragraphs:
                writer.writerow([title, p])

    json_path = os.path.join(OUTPUT_DIR, base + ".json")
    structured = [{"section": title, "paragraphs": paragraphs} for title, paragraphs in entries]
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(structured, f, indent=2)

qa_path = os.path.join(OUTPUT_DIR, "eval_qa_pairs.json")
with open(qa_path, "w", encoding="utf-8") as f:
    json.dump(qa_pairs, f, indent=2)

print(f"\nDone! Generated {len(documents)} extended documents x 6 formats + 1 Q&A file in '{OUTPUT_DIR}/'")