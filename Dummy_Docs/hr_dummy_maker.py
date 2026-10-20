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

documents = {
    "employee_handbook.pdf": [
        ("Employee Handbook", [
            "Welcome to Acme Corp. This handbook outlines the policies, procedures, and expectations for all employees.",
            "Working Hours: Standard working hours are 9:00 AM to 5:00 PM, Monday through Friday.",
            "Code of Conduct: Employees are expected to act professionally, treat colleagues with respect, and avoid conflicts of interest.",
            "Dress Code: Business casual attire is expected in the office. Casual dress is permitted on Fridays.",
            "Remote Work: Employees may work remotely up to two days per week with manager approval.",
        ]),
    ],
    "leave_policy.pdf": [
        ("Urlaubsrichtlinie / Vacation Policy", [
            "Statutory Minimum: Employees are entitled to a minimum of 24 working days of paid vacation per year based on a 6-day work week, equivalent to 20 working days for a 5-day work week.",
            "Waiting Period: Full vacation entitlement is acquired after 6 months of employment. Pro-rata entitlement applies before that.",
            "Carryover: Vacation must be taken in the current calendar year. Carryover to the next year is only permitted for compelling reasons and expires on March 31 of the following year.",
            "Illness During Vacation: If an employee falls ill during vacation and provides a medical certificate, the days of illness are not counted as vacation days.",
            "Vacation Request: Vacation requests must be submitted to the manager at least 2 weeks in advance.",
            "Special Leave: Employees are entitled to paid special leave for weddings (1 day), childbirth of spouse (1 day), and death of immediate family (2 days).",
        ]),
    ],
    "sick_leave.pdf": [
        ("Krankmeldung / Sick Leave Policy", [
            "Notification: Employees must notify their manager on the first day of illness before the start of their shift.",
            "Medical Certificate: A doctor's certificate must be submitted by the third calendar day of illness.",
            "Continued Pay: The employer continues to pay full salary for up to 6 weeks (42 calendar days) for the same illness, provided employment has lasted at least 4 weeks.",
            "Same Illness Rule: If an employee is ill with the same condition again within 6 months, the 6-week continued pay period is combined with the previous absence.",
            "Sick Leave and Vacation: Sick days are not deducted from annual vacation entitlement.",
            "Return to Work: A return-to-work conversation is held with the manager after absences longer than 6 weeks.",
        ]),
    ],
    "parental_leave.pdf": [
        ("Elternzeit / Parental Leave Policy", [
            "Entitlement: Employees are entitled to parental leave until the child's third birthday.",
            "Application: Parental leave must be requested in writing from the employer at least 7 weeks before the intended start date.",
            "Part-Time During Parental Leave: Parents may work part-time up to 30 hours per week during parental leave.",
            "Protection Against Dismissal: Employees are protected against dismissal from the start of the application period until the end of parental leave.",
            "Parental Allowance: Employees may apply for state parental allowance separately; the employer provides supporting documentation.",
            "Return to Work: Employees returning from parental leave are entitled to return to their previous position or an equivalent role.",
        ]),
    ],
    "maternity_protection.pdf": [
        ("Mutterschutz / Maternity Protection Policy", [
            "Protection Period: Pregnant employees are protected from dismissal from the start of pregnancy until 4 months after childbirth.",
            "Maternity Leave: Employees are entitled to 6 weeks before and 8 weeks after childbirth (12 weeks for premature or multiple births).",
            "Notification: Employees must inform the employer of their pregnancy and expected due date as early as possible.",
            "Workplace Adjustments: The employer must assess and adjust the workplace to protect the health of the pregnant employee.",
            "Pay During Maternity Leave: Employees receive maternity pay from health insurance plus an employer supplement.",
        ]),
    ],
    "employee_data_change.pdf": [
        ("Employee Data Change Procedure", [
            "Address Change: Employees must report a change of address to HR within 2 weeks of moving, in writing or via the HR portal.",
            "Bank Account Change: Changes to bank account details for payroll must be submitted in writing with a signed form at least 10 days before the next payroll run.",
            "Tax Class Change: Employees must submit an updated tax card to HR. Changes take effect from the month of submission.",
            "Marital Status Change: Changes to marital status affecting payroll, social security, or benefits must be reported to HR within 4 weeks.",
            "Name Change: A legal name change requires submission of an official document to HR.",
            "Emergency Contact: Employees must keep emergency contact information up to date in the HR system.",
        ]),
    ],
    "performance_review.pdf": [
        ("Performance Review Procedure", [
            "Review Cycle: Performance reviews are conducted twice per year, in June and December.",
            "Rating Scale: Employees are rated on a 5-point scale from 'Does Not Meet Expectations' to 'Outstanding'.",
            "Self-Assessment: Employees must complete a self-assessment form two weeks before the review meeting.",
            "Goal Setting: SMART goals are set at the beginning of each review cycle and tracked quarterly.",
            "Promotion Criteria: Promotions require sustained 'Exceeds Expectations' ratings for at least two consecutive cycles.",
        ]),
    ],
    "benefits_guide.pdf": [
        ("Employee Benefits Guide", [
            "Health Insurance: Acme Corp offers comprehensive medical, dental, and vision coverage.",
            "Retirement Plan: The company matches pension contributions up to 5% of salary after one year of service.",
            "Wellness Program: Employees receive a 500 EUR annual wellness stipend for gym memberships or fitness equipment.",
            "Life Insurance: Company-paid life insurance equal to 2x annual salary is provided to all full-time employees.",
            "Employee Assistance Program: Free confidential counseling is available 24/7 through our EAP partner.",
        ]),
    ],
    "workplace_conduct.pdf": [
        ("Workplace Conduct and Anti-Harassment Policy", [
            "Zero Tolerance: Acme Corp has zero tolerance for harassment, discrimination, or retaliation of any kind.",
            "Reporting: Concerns should be reported to your manager, HR, or via the anonymous ethics hotline.",
            "Investigation: All reports are investigated promptly and confidentially.",
            "Social Media: Employees must not post confidential company information or disparage colleagues online.",
            "Conflict of Interest: Employees must disclose any outside employment or financial interests that may conflict with their role.",
        ]),
    ],
    "recruitment_policy.pdf": [
        ("Recruitment and Hiring Policy", [
            "Equal Opportunity: Acme Corp is an equal opportunity employer.",
            "Job Postings: All open positions must be posted internally for at least 5 business days before external advertising.",
            "Interview Process: A minimum of two structured interviews are required for all positions.",
            "Background Checks: Employment offers are contingent on successful completion of a background check.",
            "Referral Bonus: Employees who refer a successful hire receive 2,000 EUR after the new hire completes 90 days.",
        ]),
    ],
    "onboarding_checklist.pdf": [
        ("New Employee Onboarding Checklist", [
            "Day 1: Complete HR paperwork, receive equipment, and attend orientation.",
            "Week 1: Meet your team, complete mandatory compliance training, and set up accounts.",
            "Week 2-4: Shadow a senior colleague and complete role-specific training.",
            "Day 30: Check-in meeting with your manager to review progress.",
            "Day 90: Formal probation review and goal-setting session.",
        ]),
    ],
    "training_development.pdf": [
        ("Training and Development Policy", [
            "Learning Budget: Each employee receives 1,500 EUR per year for professional development.",
            "Mandatory Training: All employees must complete annual compliance and security awareness training.",
            "Tuition Reimbursement: Up to 5,000 EUR per year is available for job-related degree programs.",
            "Certifications: The company reimburses exam fees for approved professional certifications.",
            "Internal Mobility: Employees with 12+ months of tenure may apply for internal transfers.",
        ]),
    ],
    "compensation_policy.pdf": [
        ("Compensation and Salary Structure", [
            "Pay Philosophy: Acme Corp benchmarks salaries against market data annually.",
            "Pay Bands: Each role is assigned to a pay band with a defined minimum, midpoint, and maximum salary.",
            "Annual Review: Salaries are reviewed annually in January based on performance and market adjustments.",
            "Bonuses: Discretionary annual bonuses are based on individual and company performance.",
            "Overtime: Non-exempt employees are paid 1.5x their regular rate for hours worked beyond 40 per week.",
        ]),
    ],
    "expense_reimbursement.pdf": [
        ("Expense Reimbursement Policy", [
            "Submission: Expense reports must be submitted within 30 days of the expense date with original receipts.",
            "Approval: All expenses over 500 EUR require manager approval; expenses over 2,000 EUR require director approval.",
            "Travel: Economy class is standard for flights under 6 hours.",
            "Meals: Daily meal allowance is 75 EUR for domestic travel and 100 EUR for international travel.",
            "Corporate Card: Employees traveling more than 4 times per year are issued a corporate credit card.",
        ]),
    ],
    "travel_policy.pdf": [
        ("Business Travel Policy", [
            "Booking: All business travel must be booked through the company's approved travel portal.",
            "Accommodation: Standard hotel rate is capped at 250 EUR per night in major cities.",
            "Ground Transport: Ride-sharing and rental cars are reimbursable.",
            "Advance Approval: All international travel requires VP approval at least 14 days in advance.",
            "Travel Insurance: Company-provided travel insurance covers all business trips.",
        ]),
    ],
    "it_security.pdf": [
        ("IT Security and Acceptable Use Policy", [
            "Passwords: Passwords must be at least 12 characters and rotated every 90 days.",
            "Multi-Factor Authentication: MFA is mandatory for all company systems.",
            "Device Usage: Company devices are for business use; limited personal use is permitted.",
            "Data Handling: Confidential data must not be stored on personal devices or unapproved cloud services.",
            "Incident Reporting: Suspected security incidents must be reported to IT within 1 hour.",
        ]),
    ],
    "health_safety.pdf": [
        ("Health and Safety Policy", [
            "Workplace Safety: Acme Corp is committed to providing a safe work environment for all employees.",
            "Emergency Procedures: Fire drills are conducted quarterly.",
            "First Aid: Trained first-aiders are available on each floor.",
            "Reporting Hazards: Employees must report hazards or unsafe conditions to Facilities immediately.",
            "Ergonomics: Employees may request ergonomic assessments through HR.",
        ]),
    ],
    "disciplinary_procedure.pdf": [
        ("Disciplinary Procedure", [
            "Purpose: This procedure ensures fair and consistent handling of performance or conduct issues.",
            "Verbal Warning: First-level issues are addressed through a documented verbal warning.",
            "Written Warning: Repeated or more serious issues result in a formal written warning.",
            "Final Warning: Serious misconduct may result in a final written warning.",
            "Termination: Gross misconduct or repeated violations may result in termination of employment.",
        ]),
    ],
    "grievance_policy.pdf": [
        ("Grievance Policy", [
            "Right to Raise: All employees have the right to raise grievances without fear of retaliation.",
            "Informal Resolution: Employees are encouraged to first raise concerns directly with their manager.",
            "Formal Grievance: Formal grievances must be submitted in writing to HR within 30 days of the incident.",
            "Investigation: HR will investigate and respond within 10 business days.",
            "Appeal: Employees may appeal the outcome to the HR Director within 5 business days.",
        ]),
    ],
    "diversity_inclusion.pdf": [
        ("Diversity and Inclusion Policy", [
            "Commitment: Acme Corp is committed to building a diverse and inclusive workforce.",
            "Recruitment: Hiring practices are designed to reduce unconscious bias.",
            "Employee Resource Groups: ERGs for women, LGBTQ+, veterans, and underrepresented groups are supported.",
            "Training: All managers complete annual diversity and inclusion training.",
            "Reporting: Discrimination or bias incidents should be reported to HR immediately.",
        ]),
    ],
    "overtime_policy.pdf": [
        ("Overtime Policy", [
            "Eligibility: Non-exempt employees are eligible for overtime pay at 1.5x their regular rate.",
            "Approval: All overtime must be approved in advance by a manager.",
            "Tracking: Employees must record all hours worked accurately in the time-tracking system.",
            "Maximum Hours: Employees should not exceed 60 hours of work per week without HR approval.",
            "Compensatory Time: Exempt employees may receive comp time for weekend work at manager discretion.",
        ]),
    ],
    "termination_offboarding.pdf": [
        ("Termination and Offboarding Procedure", [
            "Resignation: Employees should provide at least 2 weeks' written notice of resignation.",
            "Exit Interview: HR conducts exit interviews to gather feedback from departing employees.",
            "Equipment Return: All company equipment must be returned on the last day of employment.",
            "Final Pay: Final paychecks are issued on the next regular payday after termination.",
            "COBRA: Departing employees receive information about health insurance continuation.",
        ]),
    ],
    "referral_program.pdf": [
        ("Employee Referral Program", [
            "Eligibility: All employees except HR staff and hiring managers may participate.",
            "Bonus: A 2,000 EUR bonus is paid after the referred employee completes 90 days of employment.",
            "Exclusions: Referrals of former employees who left within the past 12 months are not eligible.",
            "Submission: Referrals must be submitted through the company careers portal.",
            "Payment: Bonuses are paid in the payroll cycle following the 90-day mark.",
        ]),
    ],
    "flexible_working.pdf": [
        ("Flexible Working Policy", [
            "Eligibility: All employees who have completed 6 months of service may request flexible working.",
            "Types: Options include remote work, compressed hours, flexitime, and part-time arrangements.",
            "Request Process: Requests must be submitted in writing to your manager 30 days in advance.",
            "Trial Period: Approved arrangements are trialed for 3 months before becoming permanent.",
            "Review: Flexible arrangements are reviewed annually as part of performance discussions.",
        ]),
    ],
    "drug_alcohol.pdf": [
        ("Drug and Alcohol Policy", [
            "Zero Tolerance: Acme Corp prohibits the use, possession, or distribution of illegal drugs on company premises.",
            "Alcohol: Alcohol may only be consumed at company-sponsored events with manager approval.",
            "Fitness for Duty: Employees must report to work free from the influence of drugs or alcohol.",
            "Testing: Drug and alcohol testing may be required for safety-sensitive roles.",
            "Support: Employees struggling with substance abuse are encouraged to contact the EAP.",
        ]),
    ],
    "data_privacy.pdf": [
        ("Data Privacy and Protection Policy", [
            "Scope: This policy covers all personal and business data collected, stored, or processed by Acme Corp.",
            "GDPR Compliance: Acme Corp complies with GDPR and other applicable data protection laws.",
            "Data Access: Employees may only access data necessary for their role.",
            "Data Breach: Suspected data breaches must be reported to the Data Protection Officer within 24 hours.",
            "Retention: Personal data is retained only as long as necessary for business or legal purposes.",
        ]),
    ],
    "exit_interview.pdf": [
        ("Exit Interview Guidelines", [
            "Purpose: Exit interviews gather feedback to improve employee experience and retention.",
            "Timing: Exit interviews are scheduled during the final week of employment.",
            "Format: Interviews may be conducted in person or via video call, lasting 30-45 minutes.",
            "Confidentiality: Feedback is aggregated and anonymized before being shared with leadership.",
            "Optional: Employees may decline an exit interview without any impact on their final pay.",
        ]),
    ],
    "relocation_policy.pdf": [
        ("Employee Relocation Policy", [
            "Eligibility: Relocation assistance is offered to employees transferring to a new location at company request.",
            "Lump Sum: A lump sum of up to 10,000 EUR is provided to cover moving costs.",
            "Temporary Housing: Up to 60 days of temporary housing is provided for relocating employees.",
            "House Hunting: One paid house-hunting trip is provided for the employee and one partner.",
            "Repayment: Relocation benefits must be repaid if the employee leaves within 12 months.",
        ]),
    ],
    "whistleblower_policy.pdf": [
        ("Whistleblower Policy", [
            "Protection: Acme Corp prohibits retaliation against employees who report concerns in good faith.",
            "Scope: Reports may cover financial fraud, safety violations, harassment, or other misconduct.",
            "Reporting Channels: Concerns may be reported to HR, Legal, or the anonymous ethics hotline.",
            "Investigation: All reports are investigated promptly and confidentially.",
            "Confidentiality: The identity of the reporter is protected to the extent permitted by law.",
        ]),
    ],
}

for filename, entries in documents.items():
    base = filename.replace(".pdf", "")
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
    print(f"Created {txt_path}")

    md = ""
    for title, paragraphs in entries:
        md += f"# {title}\n\n"
        for p in paragraphs:
            md += f"{p}\n\n"
    md_path = os.path.join(OUTPUT_DIR, base + ".md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"Created {md_path}")

    html_body = ""
    for title, paragraphs in entries:
        html_body += f"<h1>{title}</h1>\n"
        for p in paragraphs:
            html_body += f"<p>{p}</p>\n"
    html = f"<!DOCTYPE html>\n<html><head><meta charset='utf-8'><title>{base}</title></head><body>\n{html_body}</body></html>\n"
    html_path = os.path.join(OUTPUT_DIR, base + ".html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Created {html_path}")

    csv_path = os.path.join(OUTPUT_DIR, base + ".csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["section", "paragraph"])
        for title, paragraphs in entries:
            for p in paragraphs:
                writer.writerow([title, p])
    print(f"Created {csv_path}")

    json_path = os.path.join(OUTPUT_DIR, base + ".json")
    structured = [{"section": title, "paragraphs": paragraphs} for title, paragraphs in entries]
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(structured, f, indent=2)
    print(f"Created {json_path}")

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

qa_path = os.path.join(OUTPUT_DIR, "eval_qa_pairs.json")
with open(qa_path, "w", encoding="utf-8") as f:
    json.dump(qa_pairs, f, indent=2)
print(f"Created {qa_path}")

print(f"\nDone! Generated {len(documents)} documents x 6 formats + 1 Q&A file in '{OUTPUT_DIR}/'")